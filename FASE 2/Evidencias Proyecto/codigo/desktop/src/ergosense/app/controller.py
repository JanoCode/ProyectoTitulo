"""Controlador que integra aviso prolongado, inactividad y persistencia."""

from ergosense.monitoring.inactivity import BreakEventType


class MonitorController:
    """Conecta el período, el registro de actividad y la ventana."""

    def __init__(
        self,
        period,
        recorder,
        window,
        inactivity_monitor=None,
        remote_session=None,
    ):
        # Guarda los tres objetos en atributos privados.
        self._period = period
        self._recorder = recorder
        self._window = window
        self._inactivity_monitor = inactivity_monitor
        self._remote_session = remote_session

    def start(self):
        """Inicia el período y actualiza la ventana."""
        # Llama a tick de inmediato para que la ventana no espere el primer segundo.
        self._period.start()
        if self._inactivity_monitor is not None:
            self._inactivity_monitor.start()
        self.tick()

    def tick(self):
        """Avisa si se cumplió el período y actualiza los valores mostrados en la ventana."""
        self._process_inactivity()
        # Primero revisa el período: si se cumplió el límite, avisa y vuelve a cero.
        if self._period.check():
            self._window.show_alert()
        # Muestra los segundos del período y los segundos desde la última actividad.
        self._window.show_period(self._period.elapsed_seconds())
        self._window.show_last_activity(self._recorder.seconds_since_last_activity())

    def _process_inactivity(self, *, check=True):
        """Persiste transiciones y reinicia los 60 minutos solo al volver."""
        if self._inactivity_monitor is None:
            return
        if check:
            self._inactivity_monitor.check()
        for event in self._inactivity_monitor.drain_events():
            if event.event_type is BreakEventType.STARTED:
                if self._remote_session is not None:
                    self._remote_session.start_break(event.occurred_at)
            else:
                if self._remote_session is not None:
                    self._remote_session.end_break(event.occurred_at)
                # Una pausa real equivale a descanso; una inactividad breve no llega aquí.
                self._period.start()

    def finish(self):
        """Procesa el término de una pausa y cierra la sesión remota."""
        if self._inactivity_monitor is not None:
            self._inactivity_monitor.finish()
            self._process_inactivity(check=False)
        if self._remote_session is not None:
            self._remote_session.close()
