"""Controlador del monitoreo: actualiza la ventana cada segundo (Sprint 01: PB-01, PB-04 y PB-06)."""


class MonitorController:
    """Conecta el período, el registro de actividad y la ventana."""

    def __init__(self, period, recorder, window):
        # Guarda los tres objetos en atributos privados.
        self._period = period
        self._recorder = recorder
        self._window = window

    def start(self):
        """Inicia el período y actualiza la ventana."""
        # Llama a tick de inmediato para que la ventana no espere el primer segundo.
        self._period.start()
        self.tick()

    def tick(self):
        """Actualiza los valores mostrados en la ventana."""
        # Primero revisa el período: si se cumplió el límite, vuelve a cero.
        self._period.check()
        # Muestra los segundos del período y los segundos desde la última actividad.
        self._window.show_period(self._period.elapsed_seconds())
        self._window.show_last_activity(self._recorder.seconds_since_last_activity())
