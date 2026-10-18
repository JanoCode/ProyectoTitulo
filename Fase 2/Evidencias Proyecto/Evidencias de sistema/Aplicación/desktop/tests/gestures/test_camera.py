"""Pruebas del adaptador de la cámara (Sprint 03: PB-07)."""

import numpy as np

from ergosense.gestures.camera import Camera


class FakeCapture:
    """Cámara falsa: entrega los cuadros que la prueba le indica."""

    def __init__(self, opened=True, frames=None):
        self._opened = opened
        self._frames = list(frames or [])
        self.released = False

    def isOpened(self):
        return self._opened

    def read(self):
        if not self._frames:
            return False, None
        return True, self._frames.pop(0)

    def release(self):
        self.released = True


def make_camera(capture):
    return Camera(capture_factory=lambda index: capture)


def test_cp_03_01_abre_la_camara():
    camera = make_camera(FakeCapture(opened=True))
    assert camera.open() is True


def test_cp_03_02_sin_camara_disponible_no_se_abre():
    capture = FakeCapture(opened=False)
    camera = make_camera(capture)
    assert camera.open() is False
    assert capture.released is True


def test_entrega_la_imagen_en_espejo_y_en_rgb():
    # Un cuadro de 1 x 2 píxeles en BGR: azul a la izquierda y rojo a la derecha.
    bgr = np.array([[[255, 0, 0], [0, 0, 255]]], dtype=np.uint8)
    camera = make_camera(FakeCapture(frames=[bgr]))
    camera.open()
    frame = camera.read()
    # En espejo, el rojo pasa a la izquierda; en RGB, el rojo es [255, 0, 0].
    assert frame[0, 0].tolist() == [255, 0, 0]
    assert frame[0, 1].tolist() == [0, 0, 255]


def test_sin_cuadro_disponible_devuelve_none():
    camera = make_camera(FakeCapture(frames=[]))
    camera.open()
    assert camera.read() is None


def test_leer_sin_abrir_devuelve_none():
    camera = make_camera(FakeCapture())
    assert camera.read() is None


def test_close_libera_la_camara():
    capture = FakeCapture()
    camera = make_camera(capture)
    camera.open()
    camera.close()
    assert capture.released is True
