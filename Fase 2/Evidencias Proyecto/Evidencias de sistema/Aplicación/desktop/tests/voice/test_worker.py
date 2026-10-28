from ergosense.voice.worker import VoiceWorker


def test_missing_microphone_reports_error_without_crashing(monkeypatch):
    def unavailable(**kwargs):
        raise OSError("No input device")

    monkeypatch.setattr("ergosense.voice.worker.sd.RawInputStream", unavailable)
    worker = VoiceWorker()
    states = []
    worker.status_changed.connect(states.append)
    worker._run()
    assert states == ["Micrófono no disponible"]
    assert worker._stream is None


def test_stopping_without_starting_is_safe():
    worker = VoiceWorker()
    worker.stop()
    worker.stop()
    assert not worker.running
