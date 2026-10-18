"""Casos CP-02-10 a CP-02-13 de pausas por inactividad."""

from datetime import UTC, datetime, timedelta

import pytest

from ergosense.app.controller import MonitorController
from ergosense.monitoring.activity_period import ActivityPeriod
from ergosense.monitoring.activity_recorder import ActivityRecorder
from ergosense.monitoring.inactivity import BreakEventType, InactivityMonitor


class FakeTime:
    """Avanza juntos el reloj monotónico y la fecha UTC."""

    def __init__(self):
        self.seconds = 0.0
        self.origin = datetime(2026, 10, 15, 12, 0, tzinfo=UTC)

    def monotonic(self):
        return self.seconds

    def utc_now(self):
        return self.origin + timedelta(seconds=self.seconds)

    def advance(self, seconds):
        self.seconds += seconds


def make_monitor(limit_seconds=600):
    fake_time = FakeTime()
    monitor = InactivityMonitor(
        fake_time.monotonic,
        fake_time.utc_now,
        limit_seconds,
    )
    monitor.start()
    return fake_time, monitor


def test_cp_02_10_al_superar_el_limite_comienza_una_pausa():
    fake_time, monitor = make_monitor()
    fake_time.advance(600)

    monitor.check()
    events = monitor.drain_events()

    assert len(events) == 1
    assert events[0].event_type is BreakEventType.STARTED
    assert events[0].occurred_at == fake_time.origin
    assert monitor.break_active is True


def test_cp_02_11_al_retomar_actividad_termina_la_pausa():
    fake_time, monitor = make_monitor()
    fake_time.advance(600)
    monitor.check()
    monitor.drain_events()
    fake_time.advance(30)

    monitor.register_activity()
    events = monitor.drain_events()

    assert len(events) == 1
    assert events[0].event_type is BreakEventType.ENDED
    assert events[0].occurred_at == fake_time.utc_now()
    assert monitor.break_active is False


def test_cp_02_12_inactividad_breve_no_genera_una_pausa():
    fake_time, monitor = make_monitor()
    fake_time.advance(599)

    monitor.register_activity()
    monitor.check()

    assert monitor.drain_events() == []


class FakeWindow:
    def __init__(self):
        self.period = None
        self.last_activity = None
        self.alerts = 0

    def show_period(self, seconds):
        self.period = seconds

    def show_last_activity(self, seconds):
        self.last_activity = seconds

    def show_alert(self):
        self.alerts += 1


class FakeRemoteSession:
    def __init__(self):
        self.started_breaks = []
        self.ended_breaks = []

    def start_break(self, value):
        self.started_breaks.append(value)

    def end_break(self, value):
        self.ended_breaks.append(value)

    def close(self):
        pass


def test_cp_02_13_regresar_de_una_pausa_reinicia_el_periodo_de_60_minutos():
    fake_time = FakeTime()
    period = ActivityPeriod(fake_time.monotonic)
    recorder = ActivityRecorder(fake_time.monotonic)
    inactivity = InactivityMonitor(
        fake_time.monotonic,
        fake_time.utc_now,
        limit_seconds=10,
    )
    window = FakeWindow()
    remote = FakeRemoteSession()
    controller = MonitorController(period, recorder, window, inactivity, remote)
    controller.start()

    fake_time.advance(10)
    controller.tick()
    assert window.period == 10
    assert len(remote.started_breaks) == 1

    fake_time.advance(5)
    recorder.register()
    inactivity.register_activity()
    controller.tick()

    assert len(remote.ended_breaks) == 1
    assert window.period == 0


def test_cp_03_13_el_nuevo_tiempo_se_aplica_a_las_pausas_siguientes():
    fake_time, monitor = make_monitor(limit_seconds=600)
    monitor.set_limit_seconds(900)  # el usuario cambió de 10 a 15 minutos

    fake_time.advance(600)
    monitor.check()
    assert monitor.drain_events() == []  # con 10 minutos ya habría pausa

    fake_time.advance(300)
    monitor.check()
    assert [event.event_type for event in monitor.drain_events()] == [
        BreakEventType.STARTED
    ]


def test_el_tiempo_de_inactividad_debe_ser_positivo():
    _, monitor = make_monitor()
    with pytest.raises(ValueError):
        monitor.set_limit_seconds(0)
