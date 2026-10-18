"""Prueba manual de la cámara (CP-03-01 y CP-03-02).

Muestra la imagen en espejo y los cuadros por segundo. Presiona q para salir.
Ninguna imagen se guarda en disco (RNF-17).
"""

import time

import cv2

from ergosense.gestures.camera import Camera

camera = Camera()
if not camera.open():
    print("No se encontró una cámara disponible.")
    raise SystemExit(1)

print("Cámara abierta. Presiona q en la ventana para salir.")
last = time.perf_counter()
fps = 0.0
try:
    while True:
        frame = camera.read()
        if frame is None:
            continue
        now = time.perf_counter()
        fps = 0.9 * fps + 0.1 * (1 / (now - last))  # promedio suavizado
        last = now
        # imshow espera BGR, así que se vuelve a convertir solo para mostrarla.
        bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.putText(
            bgr, f"{fps:.0f} FPS", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
        )
        cv2.imshow("ErgoSense - camara", bgr)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    camera.close()
    cv2.destroyAllWindows()
