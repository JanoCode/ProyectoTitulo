import threading


class ActivityRecorder:
    def __init__(self, clock):
        self._clock = clock
        self._last = None
        self._lock = threading.Lock()

    def register(self):
        with self._lock:
            self._last = self._clock()

    def last_activity(self):
        with self._lock:
            return self._last

    def seconds_since_last_activity(self):
        with self._lock:
            if self._last is None:
                return None
            return int(self._clock() - self._last)
