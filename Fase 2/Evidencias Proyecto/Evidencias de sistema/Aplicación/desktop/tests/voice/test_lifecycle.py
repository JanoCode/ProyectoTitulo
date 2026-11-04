import json
import threading
import time
from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QApplication

from ergosense.voice.controller import VoiceController
from ergosense.voice.recognizer import VoiceModelMissing
from ergosense.voice.worker import VoiceWorker


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


def pump_until(qapp, condition):
    deadline = time.monotonic() + 2
    while not condition() and time.monotonic() < deadline:
        qapp.processEvents()
        time.sleep(0.001)
    assert condition()


def test_stop_does_not_wait_and_closes_audio(qapp):
    release = threading.Event()
    worker = VoiceWorker()
    worker._thread = threading.Thread(target=lambda: release.wait(2))
    worker._thread.start()
    stream = Mock()
    worker._stream = stream
    try:
        before = time.monotonic()
        worker.stop()
        assert time.monotonic() - before < 0.1
        assert not worker.running
        stream.abort.assert_called_once()
        stream.close.assert_called_once()
    finally:
        release.set()
        worker._thread.join(2)


def test_old_queued_results_and_status_are_discarded_after_restart(qapp):
    worker = VoiceWorker()
    commands, states = [], []
    worker.recognized.connect(commands.append)
    worker.status_changed.connect(states.append)
    old_generation = worker._generation
    thread = threading.Thread(
        target=lambda: (
            worker._result.emit(old_generation, "clic izquierdo"),
            worker._status.emit(old_generation, "Activo"),
        )
    )
    thread.start()
    thread.join(2)
    worker.stop()
    worker._stop = threading.Event()
    worker._generation += 1
    qapp.processEvents()
    assert commands == []
    assert states == ["Desactivado"]


def test_worker_delivery_runs_controller_on_ui_thread(qapp):
    worker = VoiceWorker()
    executor = Mock()
    threads = []
    controller = VoiceController(
        lambda: True, executor, Mock(), lambda: threads.append(threading.get_ident())
    )
    worker.recognized.connect(controller.handle)
    thread = threading.Thread(
        target=lambda: worker._result.emit(worker._generation, "clic izquierdo")
    )
    thread.start()
    thread.join(2)
    pump_until(qapp, lambda: bool(threads))
    assert threads == [threading.get_ident()]
    executor.submit.assert_called_once()


# --- Reconocimiento con Vosk, con un micrófono y un reconocedor falsos


class FakeRecognizer:
    """Reconocedor falso: termina una frase en el segundo bloque de audio."""

    def __init__(self, text):
        self.text = text
        self.blocks = 0

    def AcceptWaveform(self, data):
        self.blocks += 1
        return self.blocks == 2

    def Result(self):
        return json.dumps({"text": self.text})


class FakeStream:
    """Micrófono falso: entrega dos bloques de audio y después silencio."""

    def __init__(self, callback, **kwargs):
        self.callback = callback
        self.closed = False

    def __enter__(self):
        for _ in range(2):
            self.callback(b"\0" * 3200, 1600, None, None)
        return self

    def __exit__(self, *args):
        self.closed = True
        return False


def run_with(monkeypatch, recognizer):
    """Ejecuta el hilo de voz hasta reconocer una frase, o 1,5 s como máximo."""
    streams = []

    def open_stream(**kwargs):
        streams.append(FakeStream(**kwargs))
        return streams[-1]

    monkeypatch.setattr("ergosense.voice.worker.sd.RawInputStream", open_stream)
    monkeypatch.setattr(
        "ergosense.voice.worker.sd.query_devices",
        lambda kind: {"name": "Mic de prueba"},
    )
    worker = VoiceWorker(recognizer_factory=lambda: recognizer)
    texts, states, microphones = [], [], []
    worker._result.connect(lambda _, text: (texts.append(text), worker._stop.set()))
    worker._status.connect(lambda _, text: states.append(text))
    worker._microphone.connect(lambda _, name: microphones.append(name))
    timer = threading.Timer(1.5, worker._stop.set)  # por si no se reconoce nada
    timer.start()
    worker._run()
    timer.cancel()
    return texts, states, microphones, streams


def test_audio_capture_recognition_and_stop(monkeypatch, qapp):
    texts, states, microphones, streams = run_with(
        monkeypatch, FakeRecognizer("clic izquierdo")
    )
    assert texts == ["clic izquierdo"]
    assert states == ["Activo · micrófono en uso"]
    assert microphones == ["Mic de prueba"]
    assert streams[0].closed  # el micrófono se cierra al terminar


def test_silence_or_unknown_speech_is_not_reported(monkeypatch, qapp):
    texts, *_ = run_with(monkeypatch, FakeRecognizer(""))
    assert texts == []


def test_missing_model_reports_error_without_opening_the_microphone(monkeypatch, qapp):
    def missing():
        raise VoiceModelMissing("sin modelo")

    opened = []
    monkeypatch.setattr(
        "ergosense.voice.worker.sd.RawInputStream", lambda **kw: opened.append(kw)
    )
    worker = VoiceWorker(recognizer_factory=missing)
    states = []
    worker._status.connect(lambda _, text: states.append(text))
    worker._run()
    assert states == ["Falta el modelo de voz"]
    assert opened == []
