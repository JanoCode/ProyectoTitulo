import pytest

from ergosense.actions.action import Action
from ergosense.gestures.classifier import Gesture
from ergosense.gestures.control_area import control_area, cursor_area
from ergosense.gestures.cursor import CursorMapper
from ergosense.gestures.hand import Hand
from ergosense.gestures.pipeline import GesturePipeline


@pytest.mark.parametrize("side", ["left", "right"])
def test_small_side_area_maps_to_the_entire_screen(side):
    mapper = CursorMapper((0, 0, 1920, 1080), smoothing=1, dead_zone=0)
    x1, y1, x2, y2 = control_area(side, (640,480))
    mapper.set_active_rect((x1, y1, x2, y2))
    assert mapper.update((640*x1, 480*y1), (640,480)) == (0,0)
    assert mapper.update((640*x2, 480*y2), (640,480)) == (1919,1079)
    assert mapper.update((640*x1, 480*y2), (640,480)) == (0,1079)
    assert mapper.update((640*x2, 480*y1), (640,480)) == (1919,0)
    assert mapper.update((640*(x1+x2)/2, 480*(y1+y2)/2), (640,480)) == (960,540)


def hand(x, y):
    return Hand(image_points=[(x,y)]*21, world_points=[(0,0,0)]*21)


class Classifier:
    gesture = Gesture.POINT

    def classify(self, points):
        return self.gesture


@pytest.mark.parametrize("side", ["left", "right"])
@pytest.mark.parametrize("frame_size", [(640,480), (1280,720), (1920,1080)])
def test_action_rectangle_has_a_physical_aspect_of_sixteen_to_nine(side, frame_size):
    width, height = frame_size
    left, top, right, bottom = control_area(side, frame_size)
    assert (right-left)*width / ((bottom-top)*height) == pytest.approx(16/9)
    assert 0 <= left < right <= 1
    assert 0 <= top < bottom <= 1


def test_pipeline_uses_the_same_rectangle_as_the_preview():
    pipeline = GesturePipeline((0,0,1920,1080), lambda: 0, Classifier())
    pipeline.set_control_side("right")
    outside = pipeline.process(hand(480,120), (640,480))
    assert outside.gesture is Gesture.NONE
    assert outside.cursor is None
    assert pipeline._bounds == control_area("right", (640,480))


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


@pytest.mark.parametrize("side", ["left", "right"])
@pytest.mark.parametrize("corner", [(0,0), (0,1), (1,0), (1,1)])
def test_screen_corners_are_reached_before_the_hand_leaves_the_safety_area(side, corner):
    bounds = control_area(side, (640,480))
    left, top, right, bottom = cursor_area(bounds)
    assert bounds[0] < left < right < bounds[2]
    assert bounds[1] < top < bottom < bounds[3]
    pipeline = GesturePipeline((0,0,1920,1080), lambda: 0, Classifier())
    pipeline.set_control_side(side)
    center = hand((left+right)*320, (top+bottom)*240)
    for _ in range(3):
        pipeline.process(center, (640,480))
    x, y = corner
    target = hand((right if x else left)*640, (bottom if y else top)*480)
    for _ in range(100):
        step = pipeline.process(target, (640,480))
    assert step.cursor == (1919 if x else 0, 1079 if y else 0)
    assert step.gesture is Gesture.POINT


def make_stabilized_mapper():
    bounds = cursor_area(control_area("right", (640,480)))
    mapper = CursorMapper((0,0,1920,1080))
    mapper.set_active_rect(bounds)
    center = ((bounds[0]+bounds[2])*320, (bounds[1]+bounds[3])*240)
    for _ in range(6):
        mapper.update(center, (640,480))
    return mapper, center


def test_small_hand_tremor_does_not_produce_large_cursor_oscillations():
    mapper, (x,y) = make_stabilized_mapper()
    positions = [mapper.update((x+(-1)**i, y+(-1)**i), (640,480)) for i in range(120)]
    assert max(p[0] for p in positions)-min(p[0] for p in positions) <= 2
    assert max(p[1] for p in positions)-min(p[1] for p in positions) <= 2


def test_single_detection_spike_is_discarded():
    mapper, (x,y) = make_stabilized_mapper()
    assert mapper.update((x+25,y-25), (640,480)) == (960,540)
    assert mapper.update((x,y), (640,480)) == (960,540)


def test_deliberate_movement_remains_responsive_and_reset_discards_history():
    mapper, (x,y) = make_stabilized_mapper()
    for _ in range(15):
        position = mapper.update((x+25,y), (640,480))
    assert position[0] > 1190
    mapper.reset()
    assert mapper.update((x,y), (640,480)) == (960,540)
