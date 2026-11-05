"""Pérdida de conexión (Sprint 05: PB-50, CP-05-16 a CP-05-18)."""

from datetime import UTC, datetime

from ergosense.api_client import ApiClientError
from ergosense.api_client.pending import RETRY_SECONDS, PendingQueue
from ergosense.app.remote_session import RemoteUsageSession


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class Server:
    """API falsa que se puede desconectar."""

    def __init__(self):
        self.online = True
        self.calls = []
        self.health_checks = 0

    def check_connection(self):
        self.health_checks += 1
        return self.online

    def _call(self, *call):
        if not self.online:
            raise ApiClientError(
                "No fue posible conectar con el servidor de ErgoSense."
            )
        self.calls.append(call)
        return {"id": len(self.calls)}

    def start_usage_session(self, started_at):
        return self._call("start_session")

    def start_break(self, session_id, started_at):
        return self._call("start_break", session_id)

    def end_break(self, break_id, ended_at):
        return self._call("end_break", break_id)

    def end_usage_session(self, session_id, ended_at):
        return self._call("end_session", session_id)


def make():
    server, clock, changes = Server(), Clock(), []
    queue = PendingQueue(server.check_connection, clock, changes.append)
    now = datetime(2026, 11, 5, 12, 0, tzinfo=UTC)
    remote = RemoteUsageSession(server, utc_clock=lambda: now, queue=queue)
    return server, clock, changes, queue, remote, now


def test_cp_05_16_informa_la_perdida_de_conexion_y_sigue_funcionando():
    server, _, changes, queue, remote, now = make()
    remote.start()
    server.online = False
    remote.start_break(now)  # no lanza un error: el monitoreo sigue
    assert changes == [False]
    assert queue.pending == 1


def test_cp_05_17_envia_los_registros_pendientes_al_reconectar_en_orden():
    server, clock, changes, queue, remote, now = make()
    server.online = False
    remote.start()  # incluso la sesión puede crearse sin conexión
    remote.start_break(now)
    remote.end_break(now)
    server.online = True
    clock.now = RETRY_SECONDS
    queue.poll()
    # La pausa usa el id que el servidor entregó a la sesión (referencia local).
    assert server.calls == [("start_session",), ("start_break", 1), ("end_break", 2)]
    assert changes == [False, True]
    assert queue.pending == 0


def test_cp_05_18_sin_conexion_consulta_el_servidor_cada_30_segundos():
    server, clock, _, queue, remote, _ = make()
    server.online = False
    remote.start()
    for second in range(1, 91):
        clock.now = second
        queue.poll()
    assert server.health_checks == 3  # a los 30, 60 y 90 segundos


def test_una_operacion_rechazada_por_el_servidor_no_bloquea_la_cola():
    calls = []

    def rejected():
        raise ApiClientError("Ya existe una pausa en curso.", 409)

    queue = PendingQueue(lambda: True, Clock())
    queue.submit(rejected)
    queue.submit(lambda: calls.append("siguiente"))
    assert calls == ["siguiente"]
    assert queue.online is True


def test_al_cerrar_se_intenta_enviar_lo_pendiente():
    server, _, _, queue, remote, _ = make()
    server.online = False
    remote.start()
    remote.close()
    server.online = True
    queue.retry_now()
    assert server.calls == [("start_session",), ("end_session", 1)]
