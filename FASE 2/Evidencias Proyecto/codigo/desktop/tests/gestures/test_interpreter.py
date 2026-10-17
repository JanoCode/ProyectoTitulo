"""Pruebas de la interpretación de gestos (Sprint 03: PB-09 a PB-13)."""

from ergosense.actions.action import Action
from ergosense.gestures.classifier import Gesture
from ergosense.gestures.interpreter import GestureInterpreter, GestureStabilizer

L = Gesture.POINT
THUMB_IN = Gesture.THUMB_IN


class FakeClock:
    """Reloj falso: el tiempo solo avanza cuando la prueba lo indica."""

    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def make_interpreter():
    clock = FakeClock()
    return clock, GestureInterpreter(clock, hold_seconds=0.4, scroll_step=20)


# --- Estabilizador ---


def test_el_estabilizador_parte_sin_gesto():
    assert GestureStabilizer(frames=3).update(Gesture.NONE) is Gesture.NONE


def test_un_gesto_mantenido_varios_cuadros_se_acepta():
    stabilizer = GestureStabilizer(frames=3)
    results = [stabilizer.update(L) for _ in range(3)]
    assert results == [Gesture.NONE, Gesture.NONE, L]


def test_cp_03_10_un_gesto_de_un_solo_cuadro_se_ignora():
    stabilizer = GestureStabilizer(frames=3)
    for _ in range(3):
        stabilizer.update(L)
    # Un solo cuadro con el pulgar adentro, por ejemplo al pasar de una pose a otra.
    assert stabilizer.update(THUMB_IN) is L
    assert stabilizer.update(L) is L
    assert stabilizer.update(THUMB_IN) is L


# --- Movimiento del cursor ---


def test_cp_03_05_la_l_mueve_el_cursor():
    _, interpreter = make_interpreter()
    decision = interpreter.update(L)
    assert decision.move_cursor is True
    assert decision.actions == ()


def test_el_cursor_se_congela_durante_el_click():
    _, interpreter = make_interpreter()
    interpreter.update(L)
    assert interpreter.update(THUMB_IN).move_cursor is False


# --- Click izquierdo y arrastre ---


def test_cp_03_06_pulgar_adentro_y_afuera_es_click_izquierdo():
    clock, interpreter = make_interpreter()
    interpreter.update(L)
    interpreter.update(THUMB_IN)
    clock.advance(0.2)
    assert interpreter.update(L).actions == (Action.LEFT_CLICK,)


def test_cp_03_07_pulgar_mantenido_adentro_no_repite_clicks():
    clock, interpreter = make_interpreter()
    actions = []
    for _ in range(30):  # un segundo con el pulgar adentro, a 30 cuadros por segundo
        actions += interpreter.update(THUMB_IN).actions
        clock.advance(1 / 30)
    assert Action.LEFT_CLICK not in actions
    assert actions.count(Action.LEFT_DOWN) == 1


def test_cp_03_08_pulgar_adentro_mantenido_es_arrastre():
    clock, interpreter = make_interpreter()
    interpreter.update(THUMB_IN)
    clock.advance(0.4)
    decision = interpreter.update(THUMB_IN)
    assert decision.actions == (Action.LEFT_DOWN,)
    assert decision.move_cursor is True  # durante el arrastre, el cursor sigue
    assert interpreter.update(L).actions == (Action.LEFT_UP,)


def test_si_la_mano_desaparece_durante_el_arrastre_se_suelta_el_boton():
    clock, interpreter = make_interpreter()
    interpreter.update(THUMB_IN)
    clock.advance(0.5)
    interpreter.update(THUMB_IN)
    assert interpreter.update(Gesture.NONE).actions == (Action.LEFT_UP,)


# --- Click derecho ---


def test_cp_03_06_bajar_el_indice_es_un_click_derecho():
    _, interpreter = make_interpreter()
    interpreter.update(L)
    assert interpreter.update(Gesture.INDEX_DOWN).actions == (Action.RIGHT_CLICK,)


def test_cp_03_07_el_click_derecho_no_se_repite_si_se_mantiene():
    _, interpreter = make_interpreter()
    interpreter.update(Gesture.INDEX_DOWN)
    for _ in range(10):
        assert interpreter.update(Gesture.INDEX_DOWN).actions == ()
    assert interpreter.update(Gesture.INDEX_DOWN).move_cursor is False


def test_para_repetir_el_click_derecho_hay_que_subir_el_indice():
    _, interpreter = make_interpreter()
    interpreter.update(Gesture.INDEX_DOWN)
    interpreter.update(L)
    assert interpreter.update(Gesture.INDEX_DOWN).actions == (Action.RIGHT_CLICK,)


# --- Scroll ---


def test_cp_03_09_subir_la_mano_hace_scroll_hacia_arriba():
    _, interpreter = make_interpreter()
    interpreter.update(Gesture.TWO_FINGERS, hand_y=200)
    decision = interpreter.update(Gesture.TWO_FINGERS, hand_y=160)  # 2 pasos de 20
    assert decision.actions == (Action.SCROLL_UP, Action.SCROLL_UP)
    assert decision.move_cursor is False


def test_cp_03_09_bajar_la_mano_hace_scroll_hacia_abajo():
    _, interpreter = make_interpreter()
    interpreter.update(Gesture.TWO_FINGERS, hand_y=200)
    decision = interpreter.update(Gesture.TWO_FINGERS, hand_y=225)
    assert decision.actions == (Action.SCROLL_DOWN,)


def test_cp_03_09_un_movimiento_pequeno_no_hace_scroll():
    _, interpreter = make_interpreter()
    interpreter.update(Gesture.TWO_FINGERS, hand_y=200)
    assert interpreter.update(Gesture.TWO_FINGERS, hand_y=190).actions == ()


def test_el_scroll_no_pierde_el_movimiento_acumulado():
    _, interpreter = make_interpreter()
    interpreter.update(Gesture.TWO_FINGERS, hand_y=200)
    interpreter.update(Gesture.TWO_FINGERS, hand_y=190)  # 10: aún no llega a un paso
    decision = interpreter.update(Gesture.TWO_FINGERS, hand_y=180)  # 20 en total
    assert decision.actions == (Action.SCROLL_UP,)


def test_cada_scroll_nuevo_parte_desde_donde_esta_la_mano():
    _, interpreter = make_interpreter()
    interpreter.update(Gesture.TWO_FINGERS, hand_y=200)
    interpreter.update(L)
    # Al volver a hacer los dos dedos más arriba, no se cuenta el camino anterior.
    assert interpreter.update(Gesture.TWO_FINGERS, hand_y=100).actions == ()


def test_si_falta_la_altura_al_empezar_el_scroll_se_toma_en_el_cuadro_siguiente():
    _, interpreter = make_interpreter()
    interpreter.update(Gesture.TWO_FINGERS)
    assert interpreter.update(Gesture.TWO_FINGERS, hand_y=200).actions == ()
    decision = interpreter.update(Gesture.TWO_FINGERS, hand_y=180)
    assert decision.actions == (Action.SCROLL_UP,)


# --- Término ---


def test_al_terminar_en_medio_de_un_arrastre_se_suelta_el_boton():
    clock, interpreter = make_interpreter()
    interpreter.update(THUMB_IN)
    clock.advance(0.5)
    interpreter.update(THUMB_IN)
    assert interpreter.finish() == (Action.LEFT_UP,)


def test_al_terminar_con_el_pulgar_adentro_a_medias_no_hace_click():
    _, interpreter = make_interpreter()
    interpreter.update(THUMB_IN)
    assert interpreter.finish() == ()
    # Después de terminar, el intérprete parte de cero.
    assert interpreter.update(L).actions == ()


# --- Gestos sin acción ---


def test_cp_03_10_puno_y_la_l_no_hacen_nada():
    _, interpreter = make_interpreter()
    for gesture in (Gesture.FIST, Gesture.L_SHAPE, Gesture.NONE):
        decision = interpreter.update(gesture)
        assert decision.actions == ()
        assert decision.move_cursor is False
