"""Resolución de activadores de voz y gestos (PB-42 y PB-43; arquitectura, 5.5).

Los comandos y gestos predefinidos se resuelven antes; aquí llegan las frases que
no son comandos y los gestos sin acción predefinida. Si corresponden a una macro
activada y su control (voz o gestos) está activado, sus acciones se encolan en el
ejecutor único, en orden. En cualquier otro caso, no pasa nada.
"""

from PySide6.QtCore import QObject, Signal, Slot

from ergosense.macros.catalog import MACRO_GESTURES
from ergosense.macros.runner import MacroStep


class MacroController(QObject):
    # Una acción OPEN_APP sin aplicación registrada en este equipo (PB-41).
    application_missing = Signal(str)
    # Error al ejecutar una acción. Se emite desde el hilo de acciones; Qt lo
    # entrega en el de la ventana.
    failed = Signal(str)

    def __init__(self, library, executor, voice_enabled, gestures_enabled, on_activity):
        super().__init__()
        self._library = library
        self._executor = executor
        self._voice_enabled = voice_enabled
        self._gestures_enabled = gestures_enabled
        self._on_activity = on_activity

    def handle_voice(self, text):
        """Frase que no es un comando base. Devuelve True si ejecutó una macro."""
        if not self._voice_enabled():
            return False
        return self._run(self._library.find("VOICE", text))

    @Slot(str)
    def handle_gesture(self, gesture):
        """Gesto estable nuevo: se llama una vez por cada vez que se hace el gesto."""
        if gesture in MACRO_GESTURES and self._gestures_enabled():
            self._run(self._library.find("GESTURE", gesture))

    def report_error(self, message):
        self.failed.emit(message)

    def _run(self, macro):
        if macro is None:
            return False
        actions = sorted(macro["actions"], key=lambda action: action["execution_order"])
        steps = []
        for action in actions:
            kind, value = action["action_type"], action["action_value"]
            if kind == "OPEN_APP":
                path = self._library.application_path(value)
                if path is None:
                    # La ruta depende del equipo: se pide registrarla y se sigue.
                    self.application_missing.emit(value)
                    return False
                value = path
            steps.append(MacroStep(kind, value, macro["name"]))
        self._executor.submit_batch(steps)
        self._on_activity()
        return True
