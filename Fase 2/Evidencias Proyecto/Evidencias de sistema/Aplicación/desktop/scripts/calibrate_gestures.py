"""Calibración de los gestos con la mano real (SB03-T10 y SB03-T19).

Pide hacer cada gesto, mide la mano durante dos segundos y muestra en la terminal
la mediana de cada medida. Con esos valores se ajustan los umbrales de
classifier.py. Ninguna imagen se guarda (RNF-17).
"""

import math
import statistics
from collections import Counter

import cv2

from ergosense.gestures.camera import Camera
from ergosense.gestures.classifier import GestureClassifier, measure
from ergosense.gestures.hand_tracker import HandTracker

POSES = [
    "mano abierta",
    "pulgar adentro",
    "indice abajo",
    "dos dedos",
    "puno",
]
FRAMES_PER_POSE = 60  # unos dos segundos a 30 cuadros por segundo
FONT = cv2.FONT_HERSHEY_SIMPLEX
GREEN = (0, 255, 0)
# Medidas extra del pulgar: distancia de su punta a otros puntos de la palma.
THUMB_TARGETS = {"p5": 5, "p9": 9, "p13": 13, "p17": 17}


def hand_values(points):
    m = measure(points)
    size = math.dist(points[0], points[9])
    values = {
        "i": m.index,
        "m": m.middle,
        "a": m.ring,
        "me": m.pinky,
    }
    for name, target in THUMB_TARGETS.items():
        values[name] = math.dist(points[4], points[target]) / size
    return values


def show(image, lines):
    for row, text in enumerate(lines, start=1):
        cv2.putText(image, text, (10, 30 * row), FONT, 0.8, GREEN, 2)
    cv2.imshow("ErgoSense - calibracion", image)
    return cv2.waitKey(1) & 0xFF


camera = Camera()
if not camera.open():
    print("No se encontró una cámara disponible.")
    raise SystemExit(1)
tracker = HandTracker()
results = {}

try:
    for number, pose in enumerate(POSES, start=1):
        # Espera a que la persona haga el gesto y presione espacio.
        while True:
            frame = camera.read()
            if frame is None:
                continue
            hand = tracker.detect(frame)
            image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            status = "mano detectada" if hand else "sin mano"
            key = show(
                image,
                [f"{number}/5: {pose.upper()}", "Presiona ESPACIO", status],
            )
            if key == ord(" "):
                break
            if key == ord("q"):
                raise SystemExit(0)

        # Mide la pose mientras se mantiene.
        samples = []
        gestures = Counter()
        classifier = GestureClassifier()
        while len(samples) < FRAMES_PER_POSE:
            frame = camera.read()
            if frame is None:
                continue
            hand = tracker.detect(frame)
            image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            show(image, [f"{pose.upper()}: midiendo...", "Mantén el gesto"])
            if hand is None:
                continue
            samples.append(hand_values(hand.world_points))
            gestures[classifier.classify(hand.world_points).value] += 1
        results[pose] = (samples, gestures)
finally:
    tracker.close()
    camera.close()
    cv2.destroyAllWindows()

# Tabla con la mediana de cada medida por pose: es el valor "típico", sin los
# saltos ocasionales de la detección.
names = list(results[POSES[0]][0][0])  # i, m, a, me, p5, p9, p13, p17
print()
print("pose            " + "".join(f"{name:>7}" for name in names))
for pose, (samples, gestures) in results.items():
    medians = [statistics.median(sample[name] for sample in samples) for name in names]
    print(f"{pose:<16}" + "".join(f"{value:7.2f}" for value in medians))
print()
print("Gesto que reconoce hoy el clasificador en cada pose:")
for pose, (_, gestures) in results.items():
    detail = ", ".join(
        f"{gesture} {count}" for gesture, count in gestures.most_common()
    )
    print(f"  {pose:<16}{detail}")
