"""Pruebas del hilo del control por gestos (Sprint 03: PB-07 y CP-03-16).

Las pruebas llaman a run() directamente, sin crear el hilo, y usan una cámara, un
detector y un mouse falsos.
"""

import numpy as np

from ergosense.actions.action import Action
from ergosense.gestures.classifier import Gesture
from ergosense.gestures.hand import Hand
from ergosense.gestures.pipeline import GesturePipeline, Step
from ergosense.gestures.worker import MAX_MISSED_FRAMES, GestureWorker

SCREEN = (0, 0, 1920, 1080)
FRAME = np.zeros((480, 640, 3), dtype=np.uint8)
HAND = Hand(image_points=[(320.0, 240.0)] * 21, world_points=[(0.0, 0.0, 0.0)] * 21)


class FakeCamera:
    """Cámara falsa: entrega los cuadros indicados y después ninguno."""

    def __init__(self, frames=5, opened=True):
        self._frames = [FRAME] * frames
        self._opened = opened
        self.on_empty = lambda: None  # qué hacer cuando se acaban los cuadros
        self.closed = False

    def open(self):
        return self._opened

    def read(self):
        if self._frames:
            return self._frames.pop(0)
        self.on_empty()
        return None

    def close(self):
        self.closed = True


class FakeTracker:
    """Detector falso: siempre ve la misma mano."""

    def __init__(self):
        self.closed = False

    def detect(self, frame):
        return HAND

    def close(self):
        self.closed = True


class FakeClassifier:
    def __init__(self, gesture):
        self.gesture = gesture

    def classify(self, points):
        return Gesture.NONE if points is None else self.gesture


class FakeMouse:
    def __init__(self):
        self.moves = []

    def move(self, position):
        self.moves.append(position)


class FakeExecutor:
    def __init__(self):
        self.submitted = []

    def submit(self, action):
        self.submitted.append(action)


def make_worker(camera=None, pipeline=None, gesture=Gesture.POINT):
    camera = camera or FakeCamera()
    tracker = FakeTracker()
    pipeline = pipeline or GesturePipeline(
        SCREEN, lambda: 0.0, classifier=FakeClassifier(gesture)
    )
    mouse, executor = FakeMouse(), FakeExecutor()
    activity = []
    worker = GestureWorker(
        camera,
        lambda: tracker,
        pipeline,
        mouse,
        executor,
        on_activity=lambda: activity.append(True),
    )
    # Cuando la cámara falsa se queda sin cuadros, la prueba pide detener el hilo.
    camera.on_empty = worker.request_stop
    return worker, camera, tracker, mouse, executor, activity


def test_cp_03_02_sin_camara_avisa_y_no_se_cae():
    worker, *_ = make_worker(camera=FakeCamera(opened=False))
    warnings = []
    worker.camera_unavailable.connect(lambda: warnings.append(True))
    worker.run()
    assert warnings == [True]


def test_cp_03_16_la_mano_abierta_mueve_el_cursor():
    worker, _, _, mouse, _, _ = make_worker()
    worker.run()
    assert mouse.moves[-1] == (960, 540)


def test_usar_los_gestos_cuenta_como_actividad():
    worker, *_, activity = make_worker()
    worker.run()
    assert activity  # evita registrar una pausa mientras se usan los gestos


def test_avisa_a_la_ventana_solo_cuando_cambia_el_gesto():
    worker, *_ = make_worker()
    gestures = []
    worker.gesture_changed.connect(gestures.append)
    worker.run()
    # Los primeros cuadros aún no confirman el gesto; después, la mano abierta.
    assert gestures == ["none", "point"]


def test_al_terminar_libera_la_camara_y_el_detector():
    worker, camera, tracker, *_ = make_worker()
    worker.run()
    assert camera.closed is True
    assert tracker.closed is True


def test_al_terminar_entrega_al_ejecutor_las_acciones_de_cierre():
    class DraggingPipeline:
        """Tubería falsa que quedó en medio de un arrastre."""

        def process(self, hand, frame_size):
            return Step(gesture=Gesture.THUMB_IN)

        def finish(self):
            return (Action.LEFT_UP,)

    worker, _, _, _, executor, _ = make_worker(pipeline=DraggingPipeline())
    worker.run()
    assert executor.submitted == [Action.LEFT_UP]


def test_si_la_camara_deja_de_entregar_imagenes_avisa_y_termina():
    camera = FakeCamera(frames=0)
    worker, *_ = make_worker(camera=camera)
    camera.on_empty = lambda: None  # la cámara "se desconectó": nadie pide detener
    warnings = []
    worker.camera_unavailable.connect(lambda: warnings.append(True))
    worker.run()  # termina solo después de MAX_MISSED_FRAMES cuadros vacíos
    assert warnings == [True]
    assert MAX_MISSED_FRAMES > 1


def test_start_y_stop_usan_un_hilo_propio():
    worker, camera, *_ = make_worker(camera=FakeCamera(frames=1000))
    camera.on_empty = lambda: None
    worker.start()
    worker.stop()
    assert camera.closed is True
