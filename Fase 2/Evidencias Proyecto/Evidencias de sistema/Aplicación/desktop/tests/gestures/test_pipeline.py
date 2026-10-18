"""Pruebas de la cadena completa del control por gestos (Sprint 03: CP-03-16)."""

from ergosense.actions.action import Action
from ergosense.gestures.classifier import Gesture
from ergosense.gestures.hand import Hand
from ergosense.gestures.pipeline import GesturePipeline

SCREEN = (0, 0, 1920, 1080)
FRAME = (640, 480)
# Mano con todos sus puntos en el centro de la imagen: el cursor iría al centro.
HAND = Hand(image_points=[(320.0, 240.0)] * 21, world_points=[(0.0, 0.0, 0.0)] * 21)


class FakeClock:
    """Reloj falso: el tiempo solo avanza cuando la prueba lo indica."""

    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class FakeClassifier:
    """Clasificador falso: devuelve el gesto que la prueba le indica."""

    def __init__(self):
        self.gesture = Gesture.NONE

    def classify(self, points):
        return Gesture.NONE if points is None else self.gesture


def make_pipeline():
    clock = FakeClock()
    classifier = FakeClassifier()
    return clock, classifier, GesturePipeline(SCREEN, clock, classifier=classifier)


def hold(pipeline, frames=3, hand=HAND):
    """Procesa varios cuadros seguidos, como pide el estabilizador, y junta las acciones."""
    actions = []
    step = None
    for _ in range(frames):
        step = pipeline.process(hand, FRAME)
        actions += step.actions
    return step, actions


def test_cp_03_16_la_mano_abierta_mueve_el_cursor_al_punto_que_corresponde():
    _, classifier, pipeline = make_pipeline()
    classifier.gesture = Gesture.POINT
    step, _ = hold(pipeline)
    assert step.gesture is Gesture.POINT
    assert step.cursor == (960, 540)  # centro de la cámara -> centro de la pantalla


def test_sin_mano_el_cursor_no_se_mueve():
    _, _, pipeline = make_pipeline()
    step = pipeline.process(None, FRAME)
    assert step.cursor is None
    assert step.actions == ()


def test_cp_03_16_pulgar_adentro_y_afuera_hace_click_izquierdo():
    clock, classifier, pipeline = make_pipeline()
    classifier.gesture = Gesture.POINT
    hold(pipeline)
    classifier.gesture = Gesture.THUMB_IN
    hold(pipeline)
    clock.advance(0.2)
    classifier.gesture = Gesture.POINT
    _, actions = hold(pipeline)
    assert actions == [Action.LEFT_CLICK]


def test_al_terminar_durante_un_arrastre_se_suelta_el_boton():
    clock, classifier, pipeline = make_pipeline()
    classifier.gesture = Gesture.THUMB_IN
    hold(pipeline)
    clock.advance(0.5)
    hold(pipeline, frames=1)  # pasan 0,5 s con el pulgar adentro: arrastre
    assert pipeline.finish() == (Action.LEFT_UP,)
