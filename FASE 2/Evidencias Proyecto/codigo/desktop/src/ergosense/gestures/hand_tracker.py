"""Detección y seguimiento de la mano con MediaPipe Hand Landmarker (PB-07).

Entrega los 21 puntos de la mano en píxeles; el resto del módulo de gestos no
depende de MediaPipe.
"""

import time
from pathlib import Path

import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

# El modelo viaja dentro del paquete, junto a este archivo.
MODEL_PATH = Path(__file__).parent / "models" / "hand_landmarker.task"


def _create_landmarker():
    # Modo VIDEO: sigue la mano entre cuadros. Solo una mano, la que controla el cursor.
    options = vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_buffer=MODEL_PATH.read_bytes()),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.6,
        min_tracking_confidence=0.5,
    )
    return vision.HandLandmarker.create_from_options(options)


class HandTracker:
    """Busca una mano en cada cuadro y devuelve sus 21 puntos, o None si no hay mano."""

    def __init__(self, clock=time.monotonic, landmarker_factory=_create_landmarker):
        self._clock = clock
        self._landmarker = landmarker_factory()
        # Marca de tiempo del cuadro anterior, en milisegundos.
        self._last_timestamp = None

    def detect(self, frame):
        """Devuelve los 21 puntos (x, y) de la mano en píxeles, o None si no hay mano."""
        # El modo VIDEO exige marcas de tiempo que siempre aumenten: si dos cuadros
        # llegan en el mismo milisegundo, el segundo usa el milisegundo siguiente.
        timestamp = int(self._clock() * 1000)
        if self._last_timestamp is not None and timestamp <= self._last_timestamp:
            timestamp = self._last_timestamp + 1
        self._last_timestamp = timestamp

        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        result = self._landmarker.detect_for_video(image, timestamp)
        if not result.hand_landmarks:
            return None

        # MediaPipe entrega x e y entre 0 y 1; en píxeles, las distancias no se
        # deforman aunque la imagen no sea cuadrada. Se mantienen con decimales.
        height, width = frame.shape[:2]
        return [(p.x * width, p.y * height) for p in result.hand_landmarks[0]]

    def close(self):
        """Libera el detector y la memoria del modelo."""
        self._landmarker.close()
