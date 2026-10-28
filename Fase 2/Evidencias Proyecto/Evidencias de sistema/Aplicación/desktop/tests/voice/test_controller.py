from unittest.mock import Mock

import pytest

from ergosense.actions.action import Action
from ergosense.voice.controller import VoiceController


def make_controller(enabled=True):
    executor, update, activity = Mock(), Mock(), Mock()
    return (
        VoiceController(lambda: enabled, executor, update, activity),
        executor,
        update,
        activity,
    )


def test_valid_command_executes_once():
    controller, executor, update, activity = make_controller()
    controller.handle("clic izquierdo")
    executor.submit.assert_called_once_with(Action.LEFT_CLICK)
    activity.assert_called_once()
    update.assert_not_called()


@pytest.mark.parametrize("text", ["clic izquierdo", "activar gestos y voz"])
def test_disabled_voice_ignores_pending_commands(text):
    controller, executor, update, activity = make_controller(False)
    controller.handle(text)
    executor.submit.assert_not_called()
    update.assert_not_called()
    activity.assert_not_called()


@pytest.mark.parametrize(
    "text, changes",
    [
        ("activar gestos", {"gesture_enabled": True}),
        ("desactivar gestos", {"gesture_enabled": False}),
        ("activar voz", {"voice_enabled": True}),
        ("desactivar voz", {"voice_enabled": False}),
        ("activar gestos y voz", {"gesture_enabled": True, "voice_enabled": True}),
        ("desactivar gestos y voz", {"gesture_enabled": False, "voice_enabled": False}),
    ],
)
def test_toggle_commands_persist_the_expected_flags(text, changes):
    controller, executor, update, activity = make_controller()
    controller.handle(text)
    update.assert_called_once_with(changes)
    executor.submit.assert_not_called()
    activity.assert_not_called()


def test_conversation_does_not_execute_actions():
    controller, executor, update, activity = make_controller()
    controller.handle("quiero subir el volumen")
    executor.submit.assert_not_called()
    update.assert_not_called()
    activity.assert_not_called()
