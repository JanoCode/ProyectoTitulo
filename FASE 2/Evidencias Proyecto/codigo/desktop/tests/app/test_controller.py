"""Pruebas del controlador del monitoreo (Sprint 01: PB-01, PB-04 y PB-06)."""

from ergosense.app.controller import MonitorController
from ergosense.monitoring.activity_period import ActivityPeriod
from ergosense.monitoring.activity_recorder import ActivityRecorder

MINUTE = 60


class FakeClock:
    """Reloj falso: el tiempo solo avanza cuando la prueba lo indica."""

    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class FakeWindow:
    """Ventana falsa: guarda lo último que se le pidió mostrar."""

    def __init__(self):
        self.period = "sin mostrar"
        self.last_activity = "sin mostrar"

    def show_period(self, seconds):
        self.period = seconds

    def show_last_activity(self, seconds):
        self.last_activity = seconds


def make_controller():
    clock = FakeClock()
    recorder = ActivityRecorder(clock)
    window = FakeWindow()
    controller = MonitorController(ActivityPeriod(clock), recorder, window)
    return clock, recorder, window, controller


def test_cp_01_01_al_iniciar_muestra_el_periodo_en_cero():
    _, _, window, controller = make_controller()
    controller.start()
    assert window.period == 0
    assert window.last_activity is None


def test_cp_01_02_cada_tick_muestra_el_tiempo_transcurrido():
    clock, _, window, controller = make_controller()
    controller.start()
    clock.advance(5)
    controller.tick()
    assert window.period == 5


def test_muestra_los_segundos_desde_la_ultima_actividad():
    clock, recorder, window, controller = make_controller()
    controller.start()
    recorder.register()
    clock.advance(3)
    controller.tick()
    assert window.last_activity == 3


def test_cp_01_10_al_cumplir_60_minutos_el_periodo_vuelve_a_cero():
    clock, _, window, controller = make_controller()
    controller.start()
    clock.advance(60 * MINUTE)
    controller.tick()
    assert window.period == 0
