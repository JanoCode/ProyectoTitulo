"""Pruebas del registro de actividad (Sprint 01: PB-02 y PB-03)."""

from ergosense.monitoring.activity_recorder import ActivityRecorder


class FakeClock:
    """Reloj falso: el tiempo solo avanza cuando la prueba lo indica."""

    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def test_sin_actividad_no_hay_regsitro():
    recorder = ActivityRecorder(FakeClock())
    assert recorder.last_activity() is None
    assert recorder.seconds_since_last_activity() is None


def test_registra_el_momento_de_la_actividad():
    clock = FakeClock()
    recorder = ActivityRecorder(clock)
    clock.advance(30)
    recorder.register()
    assert recorder.last_activity() == 30


def test_calcula_los_segundos_desde_la_ultima_actividad():
    clock = FakeClock()
    recorder = ActivityRecorder(clock)
    recorder.register()
    clock.advance(45)
    assert recorder.seconds_since_last_activity() == 45


def test_cp_01_05_teclado_y_mouse_comparten_un_solo_registro_sin_duplicados():
    clock = FakeClock()
    recorder = ActivityRecorder(clock)
    clock.advance(10)  # registra por ejemplo un tecla
    recorder.register()

    clock.advance(5)
    recorder.register()  # registra un click
    assert recorder.last_activity() == 15
    assert recorder.seconds_since_last_activity() == 0
