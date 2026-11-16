from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from ergosense.actions.executor import ActionExecutor
from ergosense.app.controller import MonitorController
from ergosense.macros.controller import MacroController
from ergosense.monitoring.activity_period import ActivityPeriod
from ergosense.monitoring.activity_recorder import ActivityRecorder
from ergosense.monitoring.inactivity import InactivityMonitor
from ergosense.voice.controller import VoiceController


def test_simulated_day_keeps_monitoring_and_macro_action_order():
    clock, alerts, performed = [0], [], []
    now = datetime(2026, 11, 10, tzinfo=UTC)
    recorder = ActivityRecorder(lambda: clock[0])
    inactivity = InactivityMonitor(lambda: clock[0],
        lambda: now + timedelta(seconds=clock[0]), 600)
    window = SimpleNamespace(show_period=lambda value: None,
        show_last_activity=lambda value: None, show_alert=lambda: alerts.append(clock[0]))
    monitor = MonitorController(ActivityPeriod(lambda: clock[0]), recorder, window,
                                inactivity_monitor=inactivity)

    def activity():
        recorder.register()
        inactivity.register_activity()

    executor = ActionExecutor(performed.append)
    macro = {"name": "Saludo", "actions": [
        {"action_type": "TYPE_TEXT", "action_value": "A", "execution_order": 1},
        {"action_type": "TYPE_TEXT", "action_value": "B", "execution_order": 2},
    ]}
    library = SimpleNamespace(find=lambda kind, text: macro)
    macros = MacroController(library, executor, lambda: True, lambda: True, activity)
    voice = VoiceController(lambda: True, executor, lambda changes: None,
                            activity, run_macro=macros.handle_voice)
    executor.start()
    monitor.start()
    try:
        for second in range(1, 86401):
            clock[0] = second
            activity()
            monitor.tick()
            if second % 60 == 0:
                voice.handle("saludo personalizado")
                macros.handle_gesture("fist")
    finally:
        executor.stop()
    assert alerts == list(range(3600, 86401, 3600))
    assert len(performed) == 5760
    assert [step.value for step in performed] == ["A", "B"] * 2880
    assert not inactivity.break_active
    assert inactivity.drain_events() == []
