"""Pruebas de la aplicación de la configuración (Sprint 03: PB-36 y PB-37)."""

from ergosense.app.preferences import PreferencesController


class FakeGestures:
    """Hilo de gestos falso: anota cuántas veces se inicia y se detiene."""

    def __init__(self):
        self.running = False
        self.starts = 0
        self.stops = 0

    def start(self):
        self.running = True
        self.starts += 1

    def stop(self):
        self.running = False
        self.stops += 1


class FakeInactivity:
    def __init__(self):
        self.limit_seconds = None

    def set_limit_seconds(self, seconds):
        self.limit_seconds = seconds


class FakeWindow:
    def __init__(self):
        self.disabled_shown = False
        self.starting_shown = False

    def show_gestures_starting(self):
        self.starting_shown = True

    def show_gestures_disabled(self):
        self.disabled_shown = True


def settings(minutes=10, gestures=True):
    return {
        "inactivity_break_minutes": minutes,
        "voice_enabled": True,
        "gesture_enabled": gestures,
    }


def make_controller(inactivity_override=None):
    gestures, inactivity, window = FakeGestures(), FakeInactivity(), FakeWindow()
    controller = PreferencesController(
        gestures, inactivity, window, inactivity_override=inactivity_override
    )
    return controller, gestures, inactivity, window


def test_con_gestos_activados_se_inicia_el_hilo_de_gestos():
    controller, gestures, _, window = make_controller()
    controller.apply(settings(gestures=True))
    assert gestures.running is True
    assert window.starting_shown is True


def test_aplicar_dos_veces_no_abre_la_camara_otra_vez():
    controller, gestures, *_ = make_controller()
    controller.apply(settings(gestures=True))
    controller.apply(settings(gestures=True))
    assert gestures.starts == 1


def test_cp_03_12_al_desactivar_los_gestos_se_detiene_el_hilo():
    controller, gestures, _, window = make_controller()
    controller.apply(settings(gestures=True))
    controller.apply(settings(gestures=False))
    assert gestures.running is False
    assert window.disabled_shown is True


def test_cp_03_13_el_tiempo_de_inactividad_pasa_a_segundos():
    controller, _, inactivity, _ = make_controller()
    controller.apply(settings(minutes=15))
    assert inactivity.limit_seconds == 900


def test_la_variable_de_desarrollo_manda_sobre_la_configuracion():
    controller, _, inactivity, _ = make_controller(inactivity_override=10)
    controller.apply(settings(minutes=15))
    assert inactivity.limit_seconds == 10
