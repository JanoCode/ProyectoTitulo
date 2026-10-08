"""Registro de la última actividad de teclado y mouse (PB-02 y PB-03)."""

import threading


class ActivityRecorder:
    """Guarda solo el momento de la última interacción, nunca su contenido (RNF-16).

    Es seguro usarlo desde varios hilos: los listeners de teclado y mouse escriben
    y la interfaz lee, protegidos por un candado.
    """

    def __init__(self, clock):
        self._clock = clock
        self._last = None
        self._lock = threading.Lock()

    def register(self):
        """Registra que hubo actividad en este momento."""
        with self._lock:
            self._last = self._clock()

    def last_activity(self):
        """Devuelve el momento de la última actividad, o None si aún no hubo."""
        with self._lock:
            return self._last

    def seconds_since_last_activity(self):
        """Devuelve los segundos desde la última actividad, o None si aún no hubo."""
        with self._lock:
            if self._last is None:
                return None
            return int(self._clock() - self._last)
