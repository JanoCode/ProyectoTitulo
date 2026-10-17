"""Prueba manual de la detección de la mano (CP-03-03).

Dibuja los 21 puntos y muestra las distancias que usarán los gestos, en 2D y en
3D, para calibrarlas. Presiona q para salir. Ninguna imagen se guarda (RNF-17).
"""

import math
import time
from itertools import pairwise

import cv2

from ergosense.gestures.camera import Camera
from ergosense.gestures.hand_tracker import HandTracker

# Cada lista es una cadena de puntos unidos por huesos (0 es la muñeca).
CHAINS = [
    [0, 1, 2, 3, 4],  # pulgar
    [0, 5, 6, 7, 8],  # índice
    [9, 10, 11, 12],  # medio
    [13, 14, 15, 16],  # anular
    [0, 17, 18, 19, 20],  # meñique
    [5, 9, 13, 17],  # palma
]
# Puntos que usan los gestos: se dibujan con su número.
KEY_POINTS = [0, 4, 5, 6, 8, 9]
GREEN = (0, 255, 0)
FONT = cv2.FONT_HERSHEY_SIMPLEX


def write(image, text, row):
    cv2.putText(image, text, (10, 30 * row), FONT, 0.8, GREEN, 2)


def thumb_ratios(points):
    """Distancias del pulgar al costado y a la punta del índice, según el tamaño de la mano."""
    # Tamaño de la mano: de la muñeca (0) a la base del dedo medio (9).
    size = math.dist(points[0], points[9])
    side = math.dist(points[4], points[6]) / size  # click izquierdo
    tip = math.dist(points[4], points[8]) / size  # click derecho
    return side, tip


camera = Camera()
if not camera.open():
    print("No se encontró una cámara disponible.")
    raise SystemExit(1)
tracker = HandTracker()

last = time.perf_counter()
fps = 0.0
try:
    while True:
        frame = camera.read()
        if frame is None:
            continue
        hand = tracker.detect(frame)
        now = time.perf_counter()
        fps = 0.9 * fps + 0.1 * (1 / (now - last))
        last = now

        image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        write(image, f"{fps:.0f} FPS", 1)
        if hand is None:
            write(image, "Sin mano", 2)
        else:
            pixels = [(int(x), int(y)) for x, y in hand.image_points]
            for chain in CHAINS:
                # pairwise une cada punto con el siguiente: (0, 1), (1, 2), ...
                for a, b in pairwise(chain):
                    cv2.line(image, pixels[a], pixels[b], (255, 255, 255), 2)
            for number in KEY_POINTS:
                cv2.circle(image, pixels[number], 5, (0, 0, 255), -1)
                label = (pixels[number][0] + 6, pixels[number][1] - 6)
                cv2.putText(image, str(number), label, FONT, 0.5, (0, 255, 255), 1)
            # El centro de la palma (9) es el punto que sigue el cursor.
            cv2.circle(image, pixels[9], 10, GREEN, 2)
            # Se comparan las mismas distancias en 2D (imagen) y en 3D (metros).
            side_2d, tip_2d = thumb_ratios(hand.image_points)
            side_3d, tip_3d = thumb_ratios(hand.world_points)
            write(image, "              2D    3D", 2)
            write(image, f"pulgar-costado {side_2d:.2f}  {side_3d:.2f}", 3)
            write(image, f"pulgar-punta   {tip_2d:.2f}  {tip_3d:.2f}", 4)
        cv2.imshow("ErgoSense - mano", image)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    tracker.close()
    camera.close()
    cv2.destroyAllWindows()
