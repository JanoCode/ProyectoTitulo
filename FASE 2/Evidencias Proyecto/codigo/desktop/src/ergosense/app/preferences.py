"""Aplicación de la configuración del usuario a los módulos en marcha (PB-36 y PB-37).

Se usa al iniciar la aplicación, con la configuración guardada en la cuenta, y cada
vez que el usuario guarda cambios, sin necesidad de reiniciar.
"""


class PreferencesController:
    """Enciende o apaga los gestos y ajusta el tiempo de inactividad."""

    def __init__(self, gestures, inactivity, window, inactivity_override=None):
        self._gestures = gestures
        self._inactivity = inactivity
        self._window = window
        # Solo para desarrollo (ERGOSENSE_INACTIVITY_SECONDS): si existe, manda sobre la
        # configuración de la cuenta, para probar las pausas sin esperar minutos.
        self._inactivity_override = inactivity_override

    def apply(self, settings):
        """Aplica una configuración completa, como la que entrega el servidor."""
        seconds = self._inactivity_override or settings["inactivity_break_minutes"] * 60
        # El nuevo tiempo cuenta para las pausas siguientes; el aviso de 60 minutos no
        # depende de esta configuración (PB-37).
        self._inactivity.set_limit_seconds(seconds)

        if settings["gesture_enabled"]:
            # Si ya estaba funcionando, no se abre la cámara otra vez.
            if not self._gestures.running:
                self._window.show_gestures_starting()
                self._gestures.start()
        else:
            # Con los gestos desactivados, la cámara se cierra y no se ejecuta ninguna
            # acción por gestos (CP-03-12).
            self._gestures.stop()
            self._window.show_gestures_disabled()
