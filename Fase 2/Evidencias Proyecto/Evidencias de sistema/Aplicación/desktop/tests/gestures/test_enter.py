import math

import pytest
from pynput.keyboard import Key

from ergosense.actions.action import Action
from ergosense.gestures.classifier import Gesture, GestureClassifier, measure
from ergosense.gestures.interpreter import GestureInterpreter
from ergosense.macros.runner import ActionRunner

from .test_classifier import make_hand


def ok_hand(scale=1.0):
    points = make_hand(index="folded")
    points[4] = (-0.03, 0.10, 0.025)
    points[8] = (-0.025, 0.10, 0.025)
    return [tuple(value * scale for value in point) for point in points]


@pytest.mark.parametrize("scale", [0.5, 1.0, 2.0])
def test_ok_is_independent_of_hand_size_and_can_be_mirrored(scale):
    points = ok_hand(scale)
    assert GestureClassifier().classify(points) is Gesture.OK
    mirrored = [(-x, y, z) for x, y, z in points]
    assert GestureClassifier().classify(mirrored) is Gesture.OK


def test_closed_hand_does_not_become_ok_even_when_fingers_touch():
    points = make_hand(index="folded", middle="folded", ring="folded", pinky="folded", thumb="in")
    points[4] = points[8]
    assert GestureClassifier().classify(points) is not Gesture.OK
    assert GestureClassifier().classify([(0, 0, 0)] * 21) is Gesture.NONE


def test_ok_has_release_hysteresis():
    classifier = GestureClassifier()
    points = ok_hand()
    assert classifier.classify(points) is Gesture.OK
    size = math.dist(points[0], points[9])
    points[4] = (points[8][0] - size * 0.20, points[8][1], points[8][2])
    assert 0.16 < measure(points).pinch < 0.24
    assert classifier.classify(points) is Gesture.OK
    assert GestureClassifier().classify(points) is not Gesture.OK


def test_enter_requires_hold_and_open_hand_to_rearm_even_after_tracking_loss():
    now = [0.0]
    interpreter = GestureInterpreter(lambda: now[0])
    assert interpreter.update(Gesture.OK).actions == ()
    now[0] = 0.2
    assert interpreter.update(Gesture.OK).actions == ()
    now[0] = 0.4
    assert interpreter.update(Gesture.OK).actions == (Action.ENTER,)
    now[0] = 5
    assert interpreter.update(Gesture.OK).actions == ()
    interpreter.finish()
    interpreter.update(Gesture.OK)
    now[0] = 6
    assert interpreter.update(Gesture.OK).actions == ()
    interpreter.update(Gesture.POINT)
    interpreter.update(Gesture.OK)
    now[0] = 6.4
    assert interpreter.update(Gesture.OK).actions == (Action.ENTER,)


def test_approaching_ok_cancels_an_unfinished_left_click():
    now = [0.0]
    interpreter = GestureInterpreter(lambda: now[0])
    interpreter.update(Gesture.THUMB_IN)
    now[0] = .1
    assert interpreter.update(Gesture.NONE).actions == ()
    assert interpreter.update(Gesture.OK).actions == ()
    now[0] = .5
    assert interpreter.update(Gesture.OK).actions == (Action.ENTER,)


def test_enter_uses_keyboard_and_releases_key_without_mouse_actions():
    class Keyboard:
        def __init__(self):
            self.events = []

        def press(self, key):
            self.events.append(("press", key))

        def release(self, key):
            self.events.append(("release", key))

    class Mouse:
        def perform(self, action):
            raise AssertionError("Enter no es una acción del ratón")

    keyboard = Keyboard()
    assert ActionRunner(Mouse(), keyboard=keyboard).perform(Action.ENTER)
    assert keyboard.events == [("press", Key.enter), ("release", Key.enter)]
