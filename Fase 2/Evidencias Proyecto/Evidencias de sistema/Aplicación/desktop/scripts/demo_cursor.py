"""Prueba manual del movimiento del cursor (CP-03-05).

Con la mano abierta frente a la cámara, el cursor sigue el centro de la palma. Con
cualquier otro gesto, el cursor se queda quieto. Presiona q en la ventana
de la cámara para salir. Ninguna imagen se guarda (RNF-17).
"""

import ctypes

import cv2
from pynput.mouse import Controller

from ergosense.gestures.camera import Camera
from ergosense.gestures.classifier import Gesture, GestureClassifier
from ergosense.gestures.cursor import CURSOR_POINT, CursorMapper
from ergosense.gestures.hand_tracker import HandTracker

# Tamaño del monitor principal, según Windows.
user32 = ctypes.windll.user32
screen = (0, 0, user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))

camera = Camera()
if not camera.open():
    print("No se encontró una cámara disponible.")
    raise SystemExit(1)
tracker = HandTracker()
classifier = GestureClassifier()
mapper = CursorMapper(screen)
mouse = Controller()

print("Abre la mano para mover el cursor. Presiona q en la ventana de la cámara.")
try:
    while True:
        frame = camera.read()
        if frame is None:
            continue
        hand = tracker.detect(frame)
        if hand is None:
            mapper.reset()  # la mano salió: al volver, el cursor va directo a ella
            gesture = classifier.classify(None)
        else:
            gesture = classifier.classify(hand.world_points)
            if gesture is Gesture.POINT:
                height, width = frame.shape[:2]
                palm = hand.image_points[CURSOR_POINT]
                mouse.position = mapper.update(palm, (width, height))

        image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        image = cv2.resize(image, (320, 240))  # ventana chica para que no estorbe
        cv2.putText(
            image,
            gesture.value,
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )
        cv2.imshow("ErgoSense - cursor", image)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    tracker.close()
    camera.close()
    cv2.destroyAllWindows()
