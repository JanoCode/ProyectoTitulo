"""Pruebas del ciclo de vida remoto de sesiones y pausas."""

from datetime import UTC, datetime, timedelta

from ergosense.app.remote_session import RemoteUsageSession


class FakeApiClient:
    def __init__(self):
        self.calls = []

    def start_usage_session(self, started_at):
        self.calls.append(("start_session", started_at))
        return {"id": 10}

    def start_break(self, session_id, started_at):
        self.calls.append(("start_break", session_id, started_at))
        return {"id": 20}

    def end_break(self, break_id, ended_at):
        self.calls.append(("end_break", break_id, ended_at))
        return {"id": break_id}

    def end_usage_session(self, session_id, ended_at):
        self.calls.append(("end_session", session_id, ended_at))
        return {"id": session_id}


def test_cp_02_09_cerrar_aplicacion_termina_pausa_y_sesion():
    now = datetime(2026, 10, 15, 12, 0, tzinfo=UTC)
    client = FakeApiClient()
    remote = RemoteUsageSession(client, utc_clock=lambda: now + timedelta(minutes=20))
    remote.start()
    remote.start_break(now + timedelta(minutes=10))

    remote.close()

    assert [call[0] for call in client.calls] == [
        "start_session",
        "start_break",
        "end_break",
        "end_session",
    ]
