"""Ciclo de vida remoto de la sesión de uso y su pausa abierta."""

from datetime import UTC, datetime


class RemoteUsageSession:
    """Mantiene los identificadores entregados por la API durante el monitoreo."""

    def __init__(self, api_client, utc_clock=None):
        self._api_client = api_client
        self._utc_clock = utc_clock or (lambda: datetime.now(UTC))
        self._session_id = None
        self._break_id = None

    def start(self) -> None:
        """Crea la sesión que recibirá las pausas de esta ejecución."""
        if self._session_id is not None:
            return
        session = self._api_client.start_usage_session(self._utc_clock())
        self._session_id = session["id"]

    def start_break(self, started_at: datetime) -> None:
        """Guarda el inicio calculado desde la última actividad."""
        if self._session_id is None or self._break_id is not None:
            return
        pause = self._api_client.start_break(self._session_id, started_at)
        self._break_id = pause["id"]

    def end_break(self, ended_at: datetime) -> None:
        """Completa la pausa abierta al regresar la actividad."""
        if self._break_id is None:
            return
        self._api_client.end_break(self._break_id, ended_at)
        self._break_id = None

    def close(self) -> None:
        """Cierra primero la pausa y después la sesión, de forma idempotente."""
        if self._break_id is not None:
            self.end_break(self._utc_clock())
        if self._session_id is not None:
            self._api_client.end_usage_session(self._session_id, self._utc_clock())
            self._session_id = None
