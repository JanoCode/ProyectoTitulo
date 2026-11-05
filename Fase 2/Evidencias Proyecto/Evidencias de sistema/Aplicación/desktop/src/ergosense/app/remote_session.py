"""Ciclo de vida remoto de la sesión de uso y su pausa abierta.

Cada registro pasa por la cola de pendientes (PB-50): sin conexión se guarda en
memoria y se envía al volver. Como la sesión o la pausa pueden crearse sin
conexión, se usan referencias locales: el identificador del servidor se completa
cuando este responde, y las operaciones siguientes lo leen en ese momento.
"""

import time
from datetime import UTC, datetime

from ergosense.api_client.pending import PendingQueue


class _Reference:
    """Identificador que entrega el servidor; None mientras no responde."""

    id = None


class RemoteUsageSession:
    def __init__(self, api_client, utc_clock=None, queue=None):
        self._api_client = api_client
        self._utc_clock = utc_clock or (lambda: datetime.now(UTC))
        self._queue = queue or PendingQueue(lambda: False, time.monotonic)
        self._session = None
        self._break = None

    def start(self) -> None:
        """Crea la sesión que recibirá las pausas de esta ejecución."""
        if self._session is not None:
            return
        session = self._session = _Reference()
        started_at = self._utc_clock()

        def send():
            session.id = self._api_client.start_usage_session(started_at)["id"]

        self._queue.submit(send)

    def start_break(self, started_at: datetime) -> None:
        """Guarda el inicio calculado desde la última actividad."""
        if self._session is None or self._break is not None:
            return
        session, pause = self._session, _Reference()
        self._break = pause

        def send():
            if session.id is not None:  # el servidor rechazó la sesión: no hay dónde
                pause.id = self._api_client.start_break(session.id, started_at)["id"]

        self._queue.submit(send)

    def end_break(self, ended_at: datetime) -> None:
        """Completa la pausa abierta al regresar la actividad."""
        if self._break is None:
            return
        pause, self._break = self._break, None

        def send():
            if pause.id is not None:
                self._api_client.end_break(pause.id, ended_at)

        self._queue.submit(send)

    def close(self) -> None:
        """Cierra primero la pausa y después la sesión, de forma idempotente."""
        if self._break is not None:
            self.end_break(self._utc_clock())
        if self._session is not None:
            session, self._session = self._session, None
            ended_at = self._utc_clock()

            def send():
                if session.id is not None:
                    self._api_client.end_usage_session(session.id, ended_at)

            self._queue.submit(send)
