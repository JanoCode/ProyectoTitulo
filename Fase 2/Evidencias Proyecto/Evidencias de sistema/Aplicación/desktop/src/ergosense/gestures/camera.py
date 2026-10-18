"""Adaptador de la cámara web para el control mediante gestos (PB-07).

Los cuadros solo se procesan en memoria: nunca se guardan en disco ni se envían
al servidor (RNF-17).
"""

import cv2


def _open_capture(index):
    # Abre la cámara de Windows; CAP_DSHOW la abre al instante en vez de tardar segundos.
    return cv2.VideoCapture(index, cv2.CAP_DSHOW)


class Camera:
    """Abre la cámara solo cuando se pide y entrega cada cuadro listo para MediaPipe."""

    def __init__(self, index=0, capture_factory=_open_capture):
        # Solo guarda los datos: la cámara se abre recién al llamar a open().
        self._index = index
        self._capture_factory = capture_factory
        # Si es None, la cámara está cerrada; así no hace falta otro atributo de estado.
        self._capture = None

    def open(self):
        """Abre la cámara y devuelve True, o False si no hay una cámara disponible."""
        capture = self._capture_factory(self._index)
        if not capture.isOpened():
            # Se libera igual, para no dejar la cámara a medio abrir (CP-03-02).
            capture.release()
            return False
        self._capture = capture
        return True

    def read(self):
        """Devuelve el siguiente cuadro en espejo y en RGB, o None si no hay uno."""
        if self._capture is None:
            return None
        ok, frame = self._capture.read()
        if not ok:
            return None
        # Espejo: al mover la mano a la derecha, la imagen también va a la derecha.
        frame = cv2.flip(frame, 1)
        # OpenCV entrega los colores en orden BGR y MediaPipe los espera en RGB.
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def close(self):
        """Libera la cámara para que otras aplicaciones puedan usarla."""
        if self._capture is not None:
            self._capture.release()
            self._capture = None
