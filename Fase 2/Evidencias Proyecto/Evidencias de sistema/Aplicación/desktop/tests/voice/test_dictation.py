import threading
import time
from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QApplication

from ergosense.actions.text import TextInput
from ergosense.macros.runner import ActionRunner
from ergosense.voice.controller import VoiceController
from ergosense.voice.worker import VoiceWorker


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


def setup_controller():
    executor, update, activity, macros, mode = (Mock() for _ in range(5))
    controller = VoiceController(
        lambda: True, executor, update, activity, macros, mode
    )
    return controller, executor, update, activity, macros, mode


def test_commands_enable_dictation_without_typing_or_running_macro():
    controller, executor, _, _, macros, mode = setup_controller()
    controller.handle("iniciar dictado")
    mode.assert_called_once_with(True)
    controller.handle_dictation("buscar ergonomía y prevención")
    executor.submit.assert_called_once_with(
        TextInput(text="buscar ergonomía y prevención ")
    )
    macros.assert_not_called()


@pytest.mark.parametrize("text", ["clic izquierdo", "subir", "abrir correo"])
def test_commands_and_macros_are_literal_text_during_dictation(text):
    controller, executor, update, _, macros, _ = setup_controller()
    controller.set_dictation(True)
    controller.handle_dictation(text)
    executor.submit.assert_called_once_with(TextInput(text=text + " "))
    update.assert_not_called()
    macros.assert_not_called()


@pytest.mark.parametrize(
    "phrase, action",
    [
        ("enviar texto", TextInput(key="enter")),
        ("Enviar texto.", TextInput(key="enter")),
        ("nueva línea", TextInput(key="enter")),
        ("borrar palabra", TextInput(key="ctrl+backspace")),
        ("punto", TextInput(text=". ")),
        ("coma", TextInput(text=", ")),
        ("abrir interrogación", TextInput(text="¿")),
        ("quiero enviar texto mañana", TextInput(text="quiero enviar texto mañana ")),
    ],
)
def test_only_exact_editing_phrases_control_the_target(phrase, action):
    controller, executor, *_ = setup_controller()
    controller.set_dictation(True)
    controller.handle_dictation(phrase)
    executor.submit.assert_called_once_with(action)


def test_stop_discards_late_text_and_returns_to_commands():
    controller, executor, _, _, _, mode = setup_controller()
    controller.set_dictation(True)
    controller.handle_dictation("terminar dictado")
    controller.handle_dictation("texto atrasado")
    executor.submit.assert_not_called()
    assert mode.call_args_list[-1].args == (False,)
    controller.handle("clic izquierdo")
    executor.submit.assert_called_once()


def test_automatic_punctuation_does_not_break_stop_command():
    controller, executor, _, _, _, mode = setup_controller()
    controller.set_dictation(True)
    controller.handle_dictation("¡Terminar dictado!")
    mode.assert_called_with(False)
    executor.submit.assert_not_called()


@pytest.mark.parametrize("status", ["Desactivado", "Micrófono no disponible"])
def test_stopping_or_losing_microphone_cancels_dictation(status):
    controller, executor, *_ = setup_controller()
    controller.set_dictation(True)
    controller.handle_status(status)
    controller.handle_dictation("no escribir")
    executor.submit.assert_not_called()


def test_disabling_voice_still_works_while_dictating():
    controller, executor, update, *_ = setup_controller()
    controller.set_dictation(True)
    controller.handle_dictation("desactivar voz")
    update.assert_called_once_with({"voice_enabled": False})
    executor.submit.assert_not_called()


def test_empty_and_unknown_audio_do_not_type():
    controller, executor, *_ = setup_controller()
    controller.set_dictation(True)
    for text in ("", "   ", "[unk]"):
        controller.handle_dictation(text)
    executor.submit.assert_not_called()


def test_mode_revision_discards_queued_audio_even_after_round_trip(qapp):
    worker = VoiceWorker()
    texts, commands = [], []
    worker.dictated.connect(texts.append)
    worker.recognized.connect(commands.append)
    generation, revision = worker._generation, worker._mode[0]
    worker.set_dictation(True)
    old_dictation = worker._mode[0]
    worker.set_dictation(False)
    worker.set_dictation(True)
    thread = threading.Thread(target=lambda: (
        worker._scoped_result.emit(generation, revision, "clic izquierdo"),
        worker._scoped_result.emit(generation, old_dictation, "texto viejo"),
        worker._scoped_result.emit(generation, worker._mode[0], "texto actual"),
    ))
    thread.start()
    thread.join(2)
    qapp.processEvents()
    assert texts == ["texto actual"]
    assert commands == []
    worker.stop()
    worker._deliver_scoped_result(generation, worker._mode[0], "más texto")
    assert texts == ["texto actual"]


def test_indicator_events_from_an_old_mode_are_discarded(qapp):
    worker = VoiceWorker()
    states = []
    worker.dictation_state_changed.connect(states.append)
    worker.set_dictation(True)
    old = worker._mode[0]
    worker.set_dictation(False)
    worker.set_dictation(True)
    worker._deliver_dictation_state(worker._generation, old, "processing")
    worker._deliver_dictation_state(worker._generation, worker._mode[0], "listening")
    assert states == ["listening"]
    worker.stop()
    worker._deliver_dictation_state(worker._generation, worker._mode[0], "processing")
    assert states == ["listening"]


def test_loading_failure_returns_worker_to_command_mode_and_reports_it(qapp):
    worker = VoiceWorker()
    failures = []
    worker.dictation_failed.connect(failures.append)
    worker.set_dictation(True)
    worker._fail_dictation(worker._generation, "No se pudo preparar el dictado")
    assert worker._mode[1] is False
    assert failures == ["No se pudo preparar el dictado"]


def test_runner_types_unicode_and_editing_keys_without_using_clipboard():
    keyboard = Mock()
    runner = ActionRunner(Mock(), keyboard=keyboard)
    assert runner.perform(TextInput(text="prevención, niño y café "))
    keyboard.type.assert_called_once_with("prevención, niño y café ")
    assert runner.perform(TextInput(key="ctrl+backspace"))
    assert keyboard.press.call_count == keyboard.release.call_count == 2


def test_typing_failure_is_reported_and_does_not_stop_later_actions():
    keyboard, errors = Mock(), []
    keyboard.type.side_effect = OSError("input unavailable")
    runner = ActionRunner(Mock(), keyboard=keyboard, on_error=errors.append)
    assert runner.perform(TextInput(text="prueba")) is False
    assert errors == ["No se pudo escribir. Comprueba el campo de destino."]
    assert runner.perform(TextInput(key="enter"))


def test_stopping_dictation_cancels_text_already_waiting_in_executor():
    controller, executor, *_ = setup_controller()
    keyboard = Mock()
    runner = ActionRunner(Mock(), keyboard=keyboard)
    controller.set_dictation(True)
    controller.handle_dictation("texto pendiente")
    queued = executor.submit.call_args.args[0]
    controller.set_dictation(False)
    controller.set_dictation(True)
    assert runner.perform(queued)
    keyboard.type.assert_not_called()
    controller.handle_dictation("texto actual")
    assert runner.perform(executor.submit.call_args.args[0])
    keyboard.type.assert_called_once_with("texto actual ")


def test_audio_worker_switches_between_free_and_command_recognizers(monkeypatch, qapp):
    capture = []
    factories = []

    class Recognizer:
        def __init__(self, text):
            self.text = text

        def AcceptWaveform(self, data):
            return True

        def Result(self):
            import json
            return json.dumps({"text": self.text})

    class Stream:
        def __init__(self, callback, **kwargs):
            capture.append(callback)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def abort(self):
            pass

        def close(self):
            pass

    def command_factory(phrases):
        factories.append("commands")
        return Recognizer("clic izquierdo")

    def dictation_factory():
        factories.append("dictation")
        return Recognizer("buscar información")

    def wait_for(condition):
        deadline = time.monotonic() + 3
        while not condition() and time.monotonic() < deadline:
            qapp.processEvents()
            time.sleep(0.005)
        assert condition()

    monkeypatch.setattr("ergosense.voice.worker.sd.RawInputStream", Stream)
    monkeypatch.setattr("ergosense.voice.worker._input_device_name", lambda: "Test")
    worker = VoiceWorker(
        recognizer_factory=command_factory, dictation_factory=dictation_factory
    )
    texts, commands = [], []
    worker.dictated.connect(texts.append)
    worker.recognized.connect(commands.append)
    worker.start()
    try:
        wait_for(lambda: worker._stream is not None)
        worker.set_dictation(True)
        wait_for(lambda: factories[-1] == "dictation")
        capture[0](b"audio", 1, None, None)
        wait_for(lambda: bool(texts))
        assert texts == ["buscar información"]
        assert commands == []
        worker.set_dictation(False)
        wait_for(lambda: len(factories) == 3)
        capture[0](b"audio", 1, None, None)
        wait_for(lambda: bool(commands))
        assert commands == ["clic izquierdo"]
        assert factories == ["commands", "dictation", "commands"]
    finally:
        worker.stop()
        worker._thread.join(2)
