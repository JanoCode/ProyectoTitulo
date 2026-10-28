import threading
import time
from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QApplication

from ergosense.voice.controller import VoiceController
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


def test_stop_does_not_wait_for_network_and_closes_audio(qapp):
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


def test_audio_capture_recognition_and_stop(monkeypatch, qapp):
    import speech_recognition as sr

    worker = VoiceWorker()
    captured = []
    stream = Mock()
    stream.__enter__ = Mock(return_value=stream)
    stream.__exit__ = Mock(return_value=False)
    monkeypatch.setattr("ergosense.voice.worker.sd.RawInputStream", lambda **kw: stream)
    monkeypatch.setattr(
        sr.Recognizer, "listen", lambda *a, **kw: sr.AudioData(b"\0" * 32000, 16000, 2)
    )

    def transcribe(self, audio, **kwargs):
        captured.append(kwargs)
        worker._stop.set()
        return "clic izquierdo"

    monkeypatch.setattr(sr.Recognizer, "recognize_google", transcribe)
    commands = []
    worker.recognized.connect(commands.append)
    worker._run()
    assert captured[0]["language"] == "es-CL"
    assert captured[0]["endpoint"].startswith("https://")
    assert commands == []
    stream.__exit__.assert_called_once()


@pytest.mark.parametrize("failure", ["unknown", "connection", "timeout"])
def test_recognition_errors_leave_other_features_available(monkeypatch, qapp, failure):
    import speech_recognition as sr

    from ergosense.voice.worker import _AudioStopped

    worker = VoiceWorker()
    stream = Mock()
    stream.__enter__ = Mock(return_value=stream)
    stream.__exit__ = Mock(return_value=False)
    monkeypatch.setattr("ergosense.voice.worker.sd.RawInputStream", lambda **kw: stream)
    calls = []

    def listen(*args, **kwargs):
        if calls:
            raise _AudioStopped
        calls.append(True)
        return sr.AudioData(b"\0" * 32000, 16000, 2)

    def transcribe(*args, **kwargs):
        if failure == "unknown":
            raise sr.UnknownValueError
        if failure == "connection":
            raise sr.RequestError("Connection unavailable")
        raise TimeoutError

    monkeypatch.setattr(sr.Recognizer, "listen", listen)
    monkeypatch.setattr(sr.Recognizer, "recognize_google", transcribe)
    commands, states = [], []
    worker.recognized.connect(commands.append)
    worker.status_changed.connect(states.append)
    worker._run()
    assert commands == []
    if failure != "unknown":
        assert "Sin conexión" in states[-1]
    stream.__exit__.assert_called_once()
