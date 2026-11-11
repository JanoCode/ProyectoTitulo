"""Aplicación de la configuración del usuario a los módulos en marcha (PB-36 y PB-37).

Se usa al iniciar la aplicación, con la configuración guardada en la cuenta, y cada
vez que el usuario guarda cambios, sin necesidad de reiniciar.

La cámara se abre por dos motivos: porque el control con la mano está activado, o
porque el usuario la encendió solo para ver la vista previa. Con la vista previa,
los gestos no ejecutan acciones.
"""


class PreferencesController:
    """Enciende o apaga los gestos, la voz y la cámara, y ajusta la inactividad."""

    def __init__(
        self, gestures, inactivity, window, inactivity_override=None, voice=None
    ):
        self._voice = voice
        self._gestures = gestures
        self._inactivity = inactivity
        self._window = window
        # Solo para desarrollo (ERGOSENSE_INACTIVITY_SECONDS): si existe, manda sobre la
        # configuración de la cuenta, para probar las pausas sin esperar minutos.
        self._inactivity_override = inactivity_override
        # El usuario encendió la cámara para ver la vista previa.
        self._camera_requested = False

    @property
    def camera_requested(self):
        return self._camera_requested

    def apply(self, settings):
        """Aplica una configuración completa, como la que entrega el servidor."""
        seconds = self._inactivity_override or settings["inactivity_break_minutes"] * 60
        # El nuevo tiempo cuenta para las pausas siguientes; el aviso de 60 minutos no
        # depende de esta configuración (PB-37).
        self._inactivity.set_limit_seconds(seconds)
        side = settings.get("gesture_control_side", "right")
        self._gestures.set_control_side(side)
        self._window.set_control_side(side)
        if self._voice is not None:
            self._window.set_voice_enabled(settings["voice_enabled"])
            if settings["voice_enabled"]:
                self._voice.start()
            else:
                self._voice.stop()

        # Los gestos solo ejecutan acciones si están activados (CP-03-12).
        self._gestures.set_actions_enabled(settings["gesture_enabled"])
        if settings["gesture_enabled"]:
            self._window.show_gestures_starting()
            # Si la cámara ya estaba encendida, no se abre otra vez.
            if not self._gestures.running:
                self._gestures.start()
        else:
            # Sin vista previa, la cámara se cierra junto con los gestos.
            if not self._camera_requested:
                self._gestures.stop()
                self._window.show_camera_off()
            self._window.show_gestures_disabled()

    def start_camera(self):
        """Enciende la cámara para ver la vista previa, sin activar los gestos.

        Con los gestos activados, en cambio, es un reintento después de que la cámara
        no estuvo disponible: no se marca como vista previa, para que al desactivar
        los gestos la cámara se cierre como siempre.
        """
        if not self._gestures.actions_enabled:
            self._camera_requested = True
        if not self._gestures.running:
            self._window.show_camera_starting()
            self._gestures.start()

    def stop_camera(self):
        """Apaga la cámara. Si los gestos estaban activos, quien llama debe apagarlos."""
        self._camera_requested = False
        self._gestures.stop()
        self._window.show_camera_off()
