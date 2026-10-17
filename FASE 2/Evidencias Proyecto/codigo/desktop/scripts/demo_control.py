"""Prueba manual del control completo mediante gestos (CP-03-05 a CP-03-10 y CP-03-16).

Mano abierta: mover el cursor. Pulgar adentro: click izquierdo; mantenido,
arrastre. Índice abajo: click derecho. Dos dedos: scroll subiendo o bajando la
mano.

Los clicks son reales: pruébalo sobre una ventana segura, como el Paint o el
Bloc de notas. Presiona Esc en cualquier ventana para salir. Ninguna imagen se
guarda (RNF-17).
"""

import ctypes
import threading
import time

import cv2
from pynput import keyboard

from ergosense.actions.mouse import MouseActions
from ergosense.gestures.camera import Camera
from ergosense.gestures.classifier import GestureClassifier
from ergosense.gestures.cursor import CURSOR_POINT, CursorMapper
from ergosense.gestures.hand_tracker import HandTracker
from ergosense.gestures.interpreter import GestureInterpreter, GestureStabilizer

# Tamaño del monitor principal, según Windows.
user32 = ctypes.windll.user32
screen = (0, 0, user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))

# Esc detiene la prueba aunque la ventana de la cámara no tenga el foco, ya que
# los clicks pueden activar otras ventanas.
stop = threading.Event()


def on_press(key):
    if key == keyboard.Key.esc:
        stop.set()


camera = Camera()
if not camera.open():
    print("No se encontró una cámara disponible.")
    raise SystemExit(1)
tracker = HandTracker()
classifier = GestureClassifier()
stabilizer = GestureStabilizer()
interpreter = GestureInterpreter(time.monotonic)
mapper = CursorMapper(screen)
mouse = MouseActions()
listener = keyboard.Listener(on_press=on_press)
listener.start()

print("Control por gestos activo. Presiona Esc en cualquier ventana para salir.")
try:
    while not stop.is_set():
        frame = camera.read()
        if frame is None:
            continue
        hand = tracker.detect(frame)
        # Cámara -> mano -> gesto del cuadro -> gesto estable -> decisión.
        raw = classifier.classify(None if hand is None else hand.world_points)
        gesture = stabilizer.update(raw)
        palm = None if hand is None else hand.image_points[CURSOR_POINT]
        decision = interpreter.update(gesture, None if palm is None else palm[1])

        if hand is None:
            mapper.reset()  # al volver la mano, el cursor irá directo a ella
        elif decision.move_cursor:
            height, width = frame.shape[:2]
            mouse.move(mapper.update(palm, (width, height)))
        for action in decision.actions:
            mouse.perform(action)
            print("Acción:", action.value)

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
        cv2.imshow("ErgoSense - control", image)
        cv2.waitKey(1)
finally:
    # Si se sale en medio de un arrastre, el botón no puede quedar presionado.
    for action in interpreter.finish():
        mouse.perform(action)
    listener.stop()
    tracker.close()
    camera.close()
    cv2.destroyAllWindows()
