"""Detección pura de pausas por inactividad, independiente de la interfaz y red."""

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from threading import Lock


class BreakEventType(StrEnum):
    """Transiciones que deben enviarse al servidor."""

    STARTED = "started"
    ENDED = "ended"


@dataclass(frozen=True)
class BreakEvent:
    """Una transición de pausa con su fecha real en UTC."""

    event_type: BreakEventType
    occurred_at: datetime


class InactivityMonitor:
    """Detecta cuándo comienza y termina una pausa sin almacenar entradas."""

    def __init__(self, monotonic_clock, utc_clock, limit_seconds: int):
        if limit_seconds <= 0:
            raise ValueError("El límite de inactividad debe ser positivo.")
        self._monotonic_clock = monotonic_clock
        self._utc_clock = utc_clock
        self._limit_seconds = limit_seconds
        self._last_activity_monotonic = None
        self._last_activity_utc = None
        self._break_active = False
        self._events = deque()
        self._lock = Lock()

    def set_limit_seconds(self, limit_seconds: int) -> None:
        """Cambia el tiempo de inactividad; se aplica a las pausas siguientes (PB-37)."""
        if limit_seconds <= 0:
            raise ValueError("El límite de inactividad debe ser positivo.")
        with self._lock:
            # Una pausa que ya comenzó no cambia: solo cuenta para las próximas.
            self._limit_seconds = limit_seconds

    def start(self) -> None:
        """Considera el inicio del monitoreo como la actividad inicial."""
        with self._lock:
            self._last_activity_monotonic = self._monotonic_clock()
            self._last_activity_utc = self._utc_clock()
            self._break_active = False
            self._events.clear()

    def register_activity(self) -> None:
        """Registra actividad y cierra una pausa si el usuario regresó."""
        now_monotonic = self._monotonic_clock()
        now_utc = self._utc_clock()
        with self._lock:
            if self._last_activity_monotonic is None:
                self._last_activity_monotonic = now_monotonic
                self._last_activity_utc = now_utc
                return

            elapsed = now_monotonic - self._last_activity_monotonic
            # Si el usuario volvió justo antes del tick de un segundo, se crean
            # ambas transiciones para no perder una pausa que sí alcanzó el límite.
            if not self._break_active and elapsed >= self._limit_seconds:
                self._events.append(
                    BreakEvent(BreakEventType.STARTED, self._last_activity_utc)
                )
                self._break_active = True

            if self._break_active:
                self._events.append(BreakEvent(BreakEventType.ENDED, now_utc))
                self._break_active = False

            self._last_activity_monotonic = now_monotonic
            self._last_activity_utc = now_utc

    def check(self) -> None:
        """Declara una pausa una sola vez cuando se alcanza el límite."""
        with self._lock:
            if self._last_activity_monotonic is None or self._break_active:
                return
            elapsed = self._monotonic_clock() - self._last_activity_monotonic
            if elapsed >= self._limit_seconds:
                self._events.append(
                    BreakEvent(BreakEventType.STARTED, self._last_activity_utc)
                )
                self._break_active = True

    def finish(self) -> None:
        """Cierra una pausa abierta cuando se termina la aplicación."""
        with self._lock:
            if self._break_active:
                self._events.append(BreakEvent(BreakEventType.ENDED, self._utc_clock()))
                self._break_active = False

    def drain_events(self) -> list[BreakEvent]:
        """Entrega cada transición exactamente una vez al controlador."""
        with self._lock:
            events = list(self._events)
            self._events.clear()
            return events

    @property
    def break_active(self) -> bool:
        with self._lock:
            return self._break_active
