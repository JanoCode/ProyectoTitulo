"""Prueba manual del reconocimiento de gestos (CP-03-04 y CP-03-10).

Muestra el gesto reconocido y las medidas de la mano para calibrar los umbrales
de classifier.py. Presiona q para salir. Ninguna imagen se guarda (RNF-17).
"""

import cv2

from ergosense.gestures.camera import Camera
from ergosense.gestures.classifier import Gesture, GestureClassifier, measure
from ergosense.gestures.hand_tracker import HandTracker

# OpenCV no dibuja tildes ni eñes, por eso los textos van sin ellas.
LABELS = {
    Gesture.NONE: "Ninguno",
    Gesture.POINT: "L: mover",
    Gesture.PINCH: "Puntas juntas: click izquierdo",
    Gesture.INDEX_DOWN: "Indice abajo: click derecho",
    Gesture.TWO_FINGERS: "Dos dedos: scroll",
    Gesture.FIST: "Puno (macros)",
    Gesture.OPEN_HAND: "Mano abierta (macros)",
}
FONT = cv2.FONT_HERSHEY_SIMPLEX
GREEN = (0, 255, 0)


def write(image, text, row, scale=0.7):
    cv2.putText(image, text, (10, 30 * row), FONT, scale, GREEN, 2)


camera = Camera()
if not camera.open():
    print("No se encontró una cámara disponible.")
    raise SystemExit(1)
tracker = HandTracker()
classifier = GestureClassifier()

try:
    while True:
        frame = camera.read()
        if frame is None:
            continue
        hand = tracker.detect(frame)
        # Los gestos se reconocen con los puntos 3D; los 2D solo se dibujan.
        gesture = classifier.classify(None if hand is None else hand.world_points)

        image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        write(image, LABELS[gesture], 1, scale=0.9)
        if hand is not None:
            m = measure(hand.world_points)
            write(image, f"dedos  i {m.index:.2f}  m {m.middle:.2f}", 2)
            write(image, f"       a {m.ring:.2f}  me {m.pinky:.2f}", 3)
            write(image, f"pulgar abierto {m.thumb_open:.2f}", 4)
            write(image, f"pulgar punta   {m.thumb_tip:.2f}", 5)
            for x, y in hand.image_points:
                cv2.circle(image, (int(x), int(y)), 3, (0, 0, 255), -1)
        cv2.imshow("ErgoSense - gestos", image)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    tracker.close()
    camera.close()
    cv2.destroyAllWindows()
