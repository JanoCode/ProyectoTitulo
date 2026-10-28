"""Enruta comandos validados y conserva las preferencias en el servidor."""

from PySide6.QtCore import QObject, Slot

from ergosense.actions.action import Action
from ergosense.voice.commands import resolve_command


class VoiceController(QObject):
    def __init__(self, enabled, executor, update_features, on_activity):
        super().__init__()
        self._enabled = enabled
        self._executor = executor
        self._update_features = update_features
        self._on_activity = on_activity

    @Slot(str)
    def handle(self, text):
        if not self._enabled():
            return
        command = resolve_command(text)
        if isinstance(command, Action):
            self._executor.submit(command)
            self._on_activity()
            return
        changes = {
            "gestures_on": {"gesture_enabled": True},
            "gestures_off": {"gesture_enabled": False},
            "voice_on": {"voice_enabled": True},
            "voice_off": {"voice_enabled": False},
            "both_on": {"gesture_enabled": True, "voice_enabled": True},
            "both_off": {"gesture_enabled": False, "voice_enabled": False},
        }.get(command)
        if changes is not None:
            self._update_features(changes)
