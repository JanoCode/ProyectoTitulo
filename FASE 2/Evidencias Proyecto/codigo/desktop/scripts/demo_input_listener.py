"""Prueba manual de la escucha de teclado y mouse (CP-01-03 y CP-01-04).

Ejecutar con: uv run python scripts/demo_input_listener.py
"""

import time

from ergosense.monitoring.activity_recorder import ActivityRecorder
from ergosense.monitoring.input_listener import InputListener

recorder = ActivityRecorder(time.monotonic)
listener = InputListener(on_activity=recorder.register)
listener.start()

print("Escribe en cualquier ventana o haz click. La prueba dura 20 segundos...")
try:
    for _ in range(20):
        time.sleep(1)
        print(
            "Segundos desde la última actividad:",
            recorder.seconds_since_last_activity(),
        )
finally:
    listener.stop()
print("Fin de la prueba.")
