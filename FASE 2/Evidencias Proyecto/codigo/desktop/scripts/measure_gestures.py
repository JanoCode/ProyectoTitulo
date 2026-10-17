"""Medición del desempeño del control por gestos (RNF-05, RNF-06 y RNF-08).

Procesa la cámara durante el tiempo indicado (5 minutos por defecto) y al final
muestra los cuadros por segundo, el tiempo entre el gesto y la acción, y el uso
de CPU. No mueve el mouse ni hace clicks: solo mide. Ninguna imagen se guarda
(RNF-17).

Uso: uv run python scripts/measure_gestures.py [segundos]
Mientras mide, haz clicks con el pulgar y con el índice (al menos 20 en total).
Ctrl+C termina antes y muestra el resultado igual.
"""

import os
import statistics
import sys
import time

from ergosense.actions.action import Action
from ergosense.gestures.camera import Camera
from ergosense.gestures.classifier import GestureClassifier
from ergosense.gestures.cursor import CURSOR_POINT
from ergosense.gestures.hand_tracker import HandTracker
from ergosense.gestures.interpreter import GestureInterpreter, GestureStabilizer

DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 5 * 60
CLICKS = {Action.LEFT_CLICK, Action.RIGHT_CLICK}

camera = Camera()
if not camera.open():
    print("No se encontró una cámara disponible.")
    raise SystemExit(1)
tracker = HandTracker()
classifier = GestureClassifier()
stabilizer = GestureStabilizer()
interpreter = GestureInterpreter(time.monotonic)

frames_per_second = []  # cuadros procesados en cada segundo completo
processing_ms = []  # tiempo de detección y clasificación de cada cuadro
latencies_ms = []  # del cambio de pose a la acción
frames_this_second = 0
second_started = time.monotonic()
last_raw = None
raw_changed_at = time.monotonic()
start = time.monotonic()
cpu_start = time.process_time()

print(f"Midiendo durante {DURATION} s. Haz clicks con el pulgar y con el índice.")
try:
    while time.monotonic() - start < DURATION:
        frame = camera.read()
        if frame is None:
            continue
        captured = time.monotonic()
        hand = tracker.detect(frame)
        raw = classifier.classify(None if hand is None else hand.world_points)
        if raw is not last_raw:
            # El momento en que la mano cambió de pose: desde aquí se cuenta la espera.
            raw_changed_at = captured
            last_raw = raw
        gesture = stabilizer.update(raw)
        palm = None if hand is None else hand.image_points[CURSOR_POINT]
        decision = interpreter.update(gesture, None if palm is None else palm[1])
        done = time.monotonic()
        processing_ms.append((done - captured) * 1000)

        for action in decision.actions:
            # RNF-06 mide los clicks (PB-10). El arrastre espera 0,4 s a propósito y el
            # scroll depende de cuánto se mueve la mano, por eso no se cuentan.
            if action not in CLICKS:
                continue
            latency = (done - raw_changed_at) * 1000
            latencies_ms.append(latency)
            print(f"  {action.value}: {latency:.0f} ms")

        frames_this_second += 1
        if done - second_started >= 1:
            frames_per_second.append(frames_this_second)
            frames_this_second = 0
            second_started = done
            if len(frames_per_second) % 30 == 0:
                print(f"  {len(frames_per_second)} s medidos...")
except KeyboardInterrupt:
    print("Medición detenida antes de tiempo.")
finally:
    tracker.close()
    camera.close()

elapsed = time.monotonic() - start
# CPU del proceso (todos sus hilos) dividida por los núcleos: como el Administrador
# de tareas, 100 % sería el computador completo ocupado.
cpu = (time.process_time() - cpu_start) / elapsed / os.cpu_count() * 100

print()
print("Resultado")
print(f"  Duración:                 {elapsed:.0f} s")
if frames_per_second:
    print(
        f"  Cuadros por segundo:      promedio {statistics.mean(frames_per_second):.1f}, "
        f"mínimo {min(frames_per_second)}  (RNF-05: al menos 15)"
    )
print(f"  Proceso por cuadro:       promedio {statistics.mean(processing_ms):.1f} ms")
if latencies_ms:
    print(
        f"  Gesto -> acción:          {len(latencies_ms)} mediciones, "
        f"promedio {statistics.mean(latencies_ms):.0f} ms, "
        f"máximo {max(latencies_ms):.0f} ms  (RNF-06: 200 ms o menos)"
    )
else:
    print("  Gesto -> acción:          sin clicks registrados")
print(f"  CPU promedio:             {cpu:.1f} %  (RNF-08: 40 % o menos)")
