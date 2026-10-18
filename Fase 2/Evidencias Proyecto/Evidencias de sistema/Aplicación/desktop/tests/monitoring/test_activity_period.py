# Cada prueba llevara el ID de su caso en el plan de pruebas
"""Pruebas del periodo de actividad (Sprint 01: PB-01, PB-02, PB-03, PB-04, PB-05, PB-06)"""

from ergosense.monitoring.activity_period import ActivityPeriod

MINUTE = 60


class FakeClock:
    """Relog falso el tiempo solo avanza cuando la prueba lo indica"""

    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def make_period():
    clock = FakeClock()
    period = ActivityPeriod(clock)
    period.start()
    return clock, period


# FakeClock es un relgo falso el cual en las pruebas lo avanzamos con advance para ir probando el periodo de 60 min


def test_cp_01_02_el_tiempo_avanza_con_el_reloj():
    clock, period = (
        make_period()
    )  # prepara un periodo recien iniciado, para no prepetir esas lineas en cada prueba
    assert period.elapsed_seconds() == 0
    clock.advance(90)
    assert period.elapsed_seconds() == 90


def test_cp_01_06_no_avisa_antes_de_60_minutos():
    clock, period = make_period()
    clock.advance(59 * MINUTE + 59)
    assert period.check() is False


# assert es la comprobación: si lo que sigue es falso, la prueba falla.
def test_cp_01_08_el_aviso_no_se_repite_en_el_mismo_periodo():
    clock, period = make_period()
    clock.advance(60 * MINUTE)
    assert period.check() is True
    clock.advance(1)
    assert period.check() is False


def test_cp_01_10_despues_del_aviso_comienza_un_periodo_nuevo():
    clock, period = make_period()
    clock.advance(60 * MINUTE)
    period.check()
    assert period.elapsed_seconds() == 0


def test_cp_01_11_el_nuevo_periodo_mantiene_el_limite_de_60_minutos():
    clock, period = make_period()
    clock.advance(60 * MINUTE)
    period.check()
    clock.advance(59 * MINUTE)
    assert period.check() is False
    clock.advance(1 * MINUTE)
    assert period.check() is True


def test_cp_01_06_avisa_al_cumplir_60_minutos():
    clock, period = make_period()
    clock.advance(60 * MINUTE)
    assert period.check() is True
