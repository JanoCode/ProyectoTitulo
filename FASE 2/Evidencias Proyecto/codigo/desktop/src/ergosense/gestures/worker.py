"""Hilo del control por gestos (PB-07 a PB-13; arquitectura, sección 5.6).

Lee la cámara, reconoce los gestos y mueve el cursor en un hilo propio, para no
bloquear la ventana. El movimiento continuo del cursor lo aplica este hilo
directamente, por rapidez (RNF-06); los clicks y el scroll pasan por el ejecutor
único de acciones. La ventana se entera de lo que pasa mediante señales de Qt.
"""

import threading

from PySide6.QtCore import QObject, Signal

# Si la cámara deja de entregar imágenes este número de veces seguidas, por
# ejemplo porque se desconectó, se considera no disponible.
MAX_MISSED_FRAMES = 30


class GestureWorker(QObject):
    """Corre la cámara y la cadena de gestos en un hilo propio."""

    # Las señales cruzan de hilo de forma segura: la ventana las recibe en el suyo.
    gesture_changed = Signal(str)  # nombre del gesto estable, para mostrarlo
    camera_unavailable = Signal()  # no hay cámara: se informa y lo demás sigue (PB-07)

    def __init__(
        self,
        camera,
        tracker_factory,
        pipeline,
        mouse,
        executor,
        on_activity=None,
    ):
        super().__init__()
        self._camera = camera
        # Se recibe una función que crea el detector, porque conviene crearlo dentro
        # del mismo hilo que lo va a usar.
        self._tracker_factory = tracker_factory
        self._pipeline = pipeline
        self._mouse = mouse
        self._executor = executor
        # Usar los gestos también es actividad: evita que se registre una pausa falsa.
        self._on_activity = on_activity or (lambda: None)
        self._stop_requested = threading.Event()
        self._thread = None

    def start(self):
        """Abre la cámara y empieza a reconocer gestos en un hilo propio."""
        self._stop_requested.clear()
        self._thread = threading.Thread(target=self.run, name="gestos", daemon=True)
        self._thread.start()

    def request_stop(self):
        """Pide al hilo que termine después del cuadro actual."""
        self._stop_requested.set()

    def stop(self):
        """Detiene el hilo y espera a que libere la cámara."""
        self.request_stop()
        if self._thread is not None:
            self._thread.join(timeout=3)
            self._thread = None

    def run(self):
        """Ciclo del hilo: cámara -> mano -> gesto -> cursor y acciones."""
        if not self._camera.open():
            self.camera_unavailable.emit()
            return
        tracker = self._tracker_factory()
        last_gesture = None
        missed = 0
        try:
            while not self._stop_requested.is_set():
                frame = self._camera.read()
                if frame is None:
                    missed += 1
                    if missed >= MAX_MISSED_FRAMES:
                        self.camera_unavailable.emit()
                        break
                    continue
                missed = 0

                hand = tracker.detect(frame)
                height, width = frame.shape[:2]
                step = self._pipeline.process(hand, (width, height))

                if step.cursor is not None:
                    self._mouse.move(step.cursor)
                for action in step.actions:
                    self._executor.submit(action)
                if step.cursor is not None or step.actions:
                    self._on_activity()
                if step.gesture is not last_gesture:
                    self.gesture_changed.emit(step.gesture.value)
                    last_gesture = step.gesture
        finally:
            # Pase lo que pase, nunca queda el botón presionado ni la cámara abierta.
            for action in self._pipeline.finish():
                self._executor.submit(action)
            tracker.close()
            self._camera.close()
