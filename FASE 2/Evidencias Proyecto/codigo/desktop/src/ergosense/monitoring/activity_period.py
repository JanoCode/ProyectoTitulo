"""Período de actividad: controla el aviso de uso prolongado (PB-01, PB-04, PB-05 y PB-06)."""


class ActivityPeriod:
    """Cuenta el tiempo del período actual y avisa una vez al cumplirse el límite."""

    def __init__(self, clock, limit_seconds=60 * 60):
        self._clock = clock  # función que entrega la hora actual en segundos
        self._limit = (
            limit_seconds  # 60 minutos por defecto (no configurable por el usuario)
        )
        self._start = None  # momento en que comenzó el período actual

    def start(self):
        """Comienza un período nuevo."""
        # guarda en self._start la hora actual del reloj
        self._start = self._clock()

    def elapsed_seconds(self):
        """Segundos transcurridos en el período actual."""
        # devuelve (hora actual - inicio del período) como número entero
        return int(self._clock() - self._start)

    def check(self):
        """Devuelve True una sola vez al cumplirse el límite, y comienza un período nuevo."""
        # si los segundos transcurridos ya alcanzaron el límite:
        # comienza un período nuevo y devuelve True
        # si no:
        # devuelve False
        if self.elapsed_seconds() >= self._limit:
            self.start()
            return True
        return False
