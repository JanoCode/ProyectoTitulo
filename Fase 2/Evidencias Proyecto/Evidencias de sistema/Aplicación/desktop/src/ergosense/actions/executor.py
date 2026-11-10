"""Ejecutor único de acciones del sistema operativo (arquitectura, sección 5.4).

Todas las acciones discretas (clicks, arrastres y scroll) pasan por una cola que
atiende un solo hilo, en el orden en que llegaron. Así, cuando en el Sprint 04 la
voz también pida acciones, un gesto y un comando simultáneos no se intercalan.
"""

import queue
import threading

# Marca que se pone en la cola para pedirle al hilo que termine.
_STOP = object()


class ActionExecutor:
    """Ejecuta las acciones de a una, en orden de llegada, en un hilo propio."""

    def __init__(self, perform, on_error=None):
        # perform: función que ejecuta una acción, por ejemplo MouseActions.perform.
        self._perform = perform
        self._queue = queue.Queue()
        self._thread = None
        self._on_error = on_error or (lambda error: None)

    def start(self):
        """Inicia el hilo que atiende la cola."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="acciones", daemon=True)
        self._thread.start()

    def submit(self, action):
        """Agrega una acción al final de la cola; no espera a que se ejecute."""
        self._queue.put(action)

    def submit_batch(self, actions):
        self._queue.put(tuple(actions))

    def stop(self):
        """Ejecuta lo que quedó en la cola y termina el hilo."""
        if self._thread is None:
            return
        # La marca de término va al final: primero se ejecutan las acciones pendientes,
        # por ejemplo soltar el botón si se cerró la app durante un arrastre.
        self._queue.put(_STOP)
        self._thread.join(timeout=2)
        self._thread = None

    def _run(self):
        while True:
            action = self._queue.get()
            if action is _STOP:
                return
            try:
                if isinstance(action, tuple):
                    for step in action:
                        if self._perform(step) is False:
                            break
                else:
                    self._perform(action)
            except Exception as error:
                self._on_error(error)
