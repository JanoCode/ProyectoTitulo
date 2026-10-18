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

    def __init__(self, perform):
        # perform: función que ejecuta una acción, por ejemplo MouseActions.perform.
        self._perform = perform
        self._queue = queue.Queue()
        self._thread = None

    def start(self):
        """Inicia el hilo que atiende la cola."""
        self._thread = threading.Thread(target=self._run, name="acciones", daemon=True)
        self._thread.start()

    def submit(self, action):
        """Agrega una acción al final de la cola; no espera a que se ejecute."""
        self._queue.put(action)

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
            self._perform(action)
