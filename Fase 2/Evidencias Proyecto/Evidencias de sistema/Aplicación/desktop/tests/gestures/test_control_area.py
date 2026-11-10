import pytest

from ergosense.actions.action import Action
from ergosense.gestures.classifier import Gesture
from ergosense.gestures.control_area import control_area
from ergosense.gestures.cursor import CursorMapper
from ergosense.gestures.hand import Hand
from ergosense.gestures.pipeline import GesturePipeline


@pytest.mark.parametrize("side", ["left", "right"])
def test_small_side_area_maps_to_the_entire_screen(side):
    mapper = CursorMapper((0, 0, 1920, 1080), smoothing=1, dead_zone=0)
    x1, y1, x2, y2 = control_area(side)
    mapper.set_active_rect((x1, y1, x2, y2))
    assert mapper.update((640*x1, 480*y1), (640,480)) == (0,0)
    assert mapper.update((640*x2, 480*y2), (640,480)) == (1919,1079)
    assert mapper.update((640*(x1+x2)/2, 480*(y1+y2)/2), (640,480)) == (960,540)


def hand(x, y):
    return Hand(image_points=[(x,y)]*21, world_points=[(0,0,0)]*21)


class Classifier:
    gesture = Gesture.POINT

    def classify(self, points):
        return self.gesture


def test_leaving_area_cancels_click_and_requires_a_new_stable_gesture():
    clock, classifier = [0], Classifier()
    pipeline = GesturePipeline((0,0,1920,1080), lambda: clock[0], classifier)
    pipeline.set_control_side("right")
    inside, outside = hand(480,240), hand(320,240)
    classifier.gesture = Gesture.THUMB_IN
    for _ in range(3):
        pipeline.process(inside, (640,480))
    step = pipeline.process(outside, (640,480))
    assert step.actions == ()
    assert step.gesture is Gesture.NONE
    assert step.cursor is None
    assert pipeline.process(inside, (640,480)).gesture is Gesture.NONE


def test_leaving_area_releases_drag_without_clicking():
    clock, classifier = [0], Classifier()
    pipeline = GesturePipeline((0,0,1920,1080), lambda: clock[0], classifier)
    pipeline.set_control_side("right")
    classifier.gesture = Gesture.THUMB_IN
    for _ in range(3):
        pipeline.process(hand(480,240), (640,480))
    clock[0] = 1
    assert Action.LEFT_DOWN in pipeline.process(hand(480,240), (640,480)).actions
    step = pipeline.process(hand(320,240), (640,480))
    assert step.actions == (Action.LEFT_UP,)
    assert step.gesture is Gesture.NONE


def test_changing_side_resets_the_previous_gesture():
    classifier = Classifier()
    pipeline = GesturePipeline((0,0,1920,1080), lambda: 0, classifier)
    pipeline.set_control_side("right")
    for _ in range(3):
        pipeline.process(hand(480,240), (640,480))
    pipeline.set_control_side("left")
    assert pipeline.process(hand(480,240), (640,480)).cursor is None
    assert pipeline.process(hand(160,240), (640,480)).gesture is Gesture.NONE
