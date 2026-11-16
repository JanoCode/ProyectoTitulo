"""Enruta comandos validados y conserva las preferencias en el servidor."""

from dataclasses import replace
from threading import Event

from PySide6.QtCore import QObject, Signal, Slot

from ergosense.actions.action import Action
from ergosense.actions.text import TextInput
from ergosense.voice.commands import normalize, resolve_command


class VoiceController(QObject):
    dictation_changed = Signal(bool)

    def __init__(
        self, enabled, executor, update_features, on_activity, run_macro=None,
        set_dictation=None,
    ):
        super().__init__()
        self._enabled = enabled
        self._executor = executor
        self._update_features = update_features
        self._on_activity = on_activity
        # Si la frase no es un comando base, puede activar una macro (PB-42).
        self._run_macro = run_macro or (lambda text: False)
        self._set_dictation = set_dictation or (lambda active: None)
        self._dictating = False
        self._dictation_cancelled = Event()
        self._dictation_cancelled.set()

    @Slot(bool)
    def set_dictation(self, active):
        active = bool(active and self._enabled())
        if self._dictating != active:
            self._dictation_cancelled.set()
            if active:
                self._dictation_cancelled = Event()
            self._dictating = active
            self._set_dictation(active)
            self.dictation_changed.emit(active)

    @Slot(str)
    def handle_status(self, status):
        if status != "Activo · micrófono en uso":
            self.set_dictation(False)

    @Slot(str)
    def handle_dictation(self, text):
        if not self._enabled() or not self._dictating:
            return
        phrase = normalize(text).strip(" .,!¡?¿:;\"'«»")
        if phrase in {"terminar dictado", "desactivar dictado"}:
            self.set_dictation(False)
            return
        if phrase in {"desactivar voz", "desactivar gestos y voz"}:
            self.set_dictation(False)
            self.handle(text)
            return
        keys = {
            "enviar texto": "enter",
            "borrar palabra": "ctrl+backspace",
            "nueva linea": "enter",
        }
        punctuation = {
            "punto": ". ", "coma": ", ", "dos puntos": ": ",
            "punto y coma": "; ", "abrir interrogacion": "¿",
            "cerrar interrogacion": "? ",
        }
        if phrase in keys:
            action = TextInput(key=keys[phrase])
        else:
            clean = " ".join(text.replace("[unk]", "").split())
            if not clean:
                return
            action = TextInput(text=punctuation.get(phrase, clean + " "))
        self._executor.submit(replace(action, cancelled=self._dictation_cancelled))
        self._on_activity()

    @Slot(str)
    def handle(self, text):
        if not self._enabled():
            return
        if self._dictating:
            return
        command = resolve_command(text)
        if command == "dictation_on":
            self.set_dictation(True)
            return
        if command is None:
            # Primero los comandos base; después las macros (arquitectura, 5.5).
            self._run_macro(text)
            return
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
