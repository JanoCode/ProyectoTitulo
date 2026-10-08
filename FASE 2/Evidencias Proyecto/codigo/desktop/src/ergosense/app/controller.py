"""Controlador del monitoreo: actualiza la ventana cada segundo y avisa al cumplirse el período (Sprint 01: PB-01, PB-04, PB-05 y PB-06)."""


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
        """Avisa si se cumplió el período y actualiza los valores mostrados en la ventana."""
        # Primero revisa el período: si se cumplió el límite, avisa y vuelve a cero.
        if self._period.check():
            self._window.show_alert()
        # Muestra los segundos del período y los segundos desde la última actividad.
        self._window.show_period(self._period.elapsed_seconds())
        self._window.show_last_activity(self._recorder.seconds_since_last_activity())
