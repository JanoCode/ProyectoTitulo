"""Pruebas de la detección de la mano (Sprint 03: PB-07)."""

import numpy as np

from ergosense.gestures.hand_tracker import HandTracker


class FakeClock:
    """Reloj falso: el tiempo solo avanza cuando la prueba lo indica."""

    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class FakePoint:
    """Punto como los de MediaPipe: en la imagen, x e y van de 0 a 1; en 3D, metros."""

    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z


class FakeResult:
    def __init__(self, hands, world_hands):
        self.hand_landmarks = hands
        self.hand_world_landmarks = world_hands


class FakeLandmarker:
    """Detector falso: siempre ve las manos indicadas y anota las marcas de tiempo."""

    def __init__(self, hands=None, world_hands=None):
        self._hands = hands or []
        self._world_hands = world_hands or []
        self.timestamps = []
        self.closed = False

    def detect_for_video(self, image, timestamp_ms):
        self.timestamps.append(timestamp_ms)
        return FakeResult(self._hands, self._world_hands)

    def close(self):
        self.closed = True


def make_tracker(landmarker, clock=None):
    return HandTracker(
        clock=clock or FakeClock(), landmarker_factory=lambda: landmarker
    )


def black_frame(height=100, width=200):
    return np.zeros((height, width, 3), dtype=np.uint8)


def make_landmarker_with_hand():
    image_hand = [FakePoint(0.5, 0.25)] * 21
    world_hand = [FakePoint(0.01, 0.02, 0.03)] * 21
    return FakeLandmarker(hands=[image_hand], world_hands=[world_hand])


def test_cp_03_03_entrega_los_21_puntos_en_pixeles():
    tracker = make_tracker(make_landmarker_with_hand())
    hand = tracker.detect(black_frame(height=100, width=200))
    assert len(hand.image_points) == 21
    # La mitad de 200 de ancho y un cuarto de 100 de alto.
    assert hand.image_points[0] == (100.0, 25.0)


def test_entrega_los_21_puntos_en_3d_en_metros():
    tracker = make_tracker(make_landmarker_with_hand())
    hand = tracker.detect(black_frame())
    assert len(hand.world_points) == 21
    assert hand.world_points[0] == (0.01, 0.02, 0.03)


def test_sin_mano_devuelve_none():
    tracker = make_tracker(FakeLandmarker(hands=[]))
    assert tracker.detect(black_frame()) is None


def test_las_marcas_de_tiempo_siempre_avanzan():
    clock = FakeClock()
    landmarker = FakeLandmarker()
    tracker = make_tracker(landmarker, clock)
    tracker.detect(black_frame())
    tracker.detect(black_frame())  # mismo milisegundo: debe usar el siguiente
    clock.advance(0.5)
    tracker.detect(black_frame())
    assert landmarker.timestamps == [0, 1, 500]


def test_close_cierra_el_detector():
    landmarker = FakeLandmarker()
    tracker = make_tracker(landmarker)
    tracker.close()
    assert landmarker.closed is True


def test_el_modelo_real_carga_y_no_ve_manos_en_una_imagen_negra():
    tracker = HandTracker()
    try:
        assert tracker.detect(black_frame(480, 640)) is None
    finally:
        tracker.close()
