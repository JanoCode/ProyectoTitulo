"""Hilo del control por gestos (PB-07 a PB-13; arquitectura, sección 5.6).

Lee la cámara, reconoce los gestos y mueve el cursor en un hilo propio, para no
bloquear la ventana. El movimiento continuo del cursor lo aplica este hilo
directamente, por rapidez (RNF-06); los clicks y el scroll pasan por el ejecutor
único de acciones. La ventana se entera de lo que pasa mediante señales de Qt, y
recibe cada cuadro para la vista previa. Las imágenes solo viajan en memoria:
nunca se guardan ni se envían al servidor (RNF-17).
"""

import threading

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage

# Si la cámara deja de entregar imágenes este número de veces seguidas, por
# ejemplo porque se desconectó, se considera no disponible. Entre un intento y el
# siguiente se espera un poco: así se tolera una falla de unos 3 segundos, como un
# tropiezo del USB, en vez de darla por perdida en un instante.
MAX_MISSED_FRAMES = 30
MISSED_FRAME_WAIT = 0.1  # segundos


def _to_qimage(frame):
    """Convierte un cuadro RGB de numpy en una QImage propia para la ventana."""
    height, width = frame.shape[:2]
    image = QImage(
        frame.data, width, height, frame.strides[0], QImage.Format.Format_RGB888
    )
    # copy(): la imagen debe tener sus propios datos, porque el cuadro se reutiliza.
    return image.copy()


class GestureWorker(QObject):
    """Corre la cámara y la cadena de gestos en un hilo propio."""

    # Las señales cruzan de hilo de forma segura: la ventana las recibe en el suyo.
    gesture_changed = Signal(str)  # nombre del gesto estable, para mostrarlo
    camera_unavailable = Signal()  # no hay cámara: se informa y lo demás sigue (PB-07)
    hand_changed = Signal(bool)  # la mano apareció o salió de la imagen
    # Cuadro para la vista previa y puntos de la mano entre 0 y 1 (o None sin mano).
    frame_ready = Signal(QImage, object)

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
        # Con las acciones apagadas, la cámara solo sirve de vista previa.
        self._actions_enabled = True

    @property
    def actions_enabled(self):
        return self._actions_enabled

    def set_actions_enabled(self, enabled):
        """Decide si los gestos mueven el cursor y hacen clicks, o solo se muestran."""
        self._actions_enabled = enabled

    def start(self):
        """Abre la cámara y empieza a reconocer gestos en un hilo propio."""
        if self.running:
            return
        self._stop_requested.clear()
        self._thread = threading.Thread(target=self.run, name="gestos", daemon=True)
        self._thread.start()

    @property
    def running(self):
        """Indica si el hilo de gestos está funcionando."""
        return self._thread is not None and self._thread.is_alive()

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
        tracker = None
        last_gesture = None
        had_hand = None
        acting = self._actions_enabled
        missed = 0
        try:
            tracker = self._tracker_factory()
            while not self._stop_requested.is_set():
                frame = self._camera.read()
                if frame is None:
                    missed += 1
                    if missed >= MAX_MISSED_FRAMES:
                        self.camera_unavailable.emit()
                        break
                    # wait() y no sleep(): si se pide detener, termina de inmediato.
                    self._stop_requested.wait(MISSED_FRAME_WAIT)
                    continue
                missed = 0

                hand = tracker.detect(frame)
                height, width = frame.shape[:2]
                step = self._pipeline.process(hand, (width, height))

                enabled = self._actions_enabled
                if enabled:
                    if step.cursor is not None:
                        self._mouse.move(step.cursor)
                    for action in step.actions:
                        self._executor.submit(action)
                    if step.cursor is not None or step.actions:
                        self._on_activity()
                elif acting:
                    # Se acaban de apagar las acciones: se termina limpio, por ejemplo
                    # soltando el botón si había un arrastre.
                    for action in self._pipeline.finish():
                        self._executor.submit(action)
                acting = enabled

                if step.gesture is not last_gesture:
                    self.gesture_changed.emit(step.gesture.value)
                    last_gesture = step.gesture
                if (hand is not None) is not had_hand:
                    had_hand = hand is not None
                    self.hand_changed.emit(had_hand)
                points = None
                if hand is not None:
                    points = [(x / width, y / height) for x, y in hand.image_points]
                self.frame_ready.emit(_to_qimage(frame), points)
        except (OSError, RuntimeError, ValueError):
            self.camera_unavailable.emit()
        finally:
            # Pase lo que pase, nunca queda el botón presionado ni la cámara abierta.
            try:
                for action in self._pipeline.finish():
                    self._executor.submit(action)
            finally:
                try:
                    if tracker is not None:
                        tracker.close()
                finally:
                    self._camera.close()
