from ergosense.voice.worker import VoiceWorker


def test_missing_microphone_reports_error_without_crashing(monkeypatch):
    def unavailable(**kwargs):
        raise OSError("No input device")

    monkeypatch.setattr("ergosense.voice.worker.sd.RawInputStream", unavailable)
    worker = VoiceWorker(recognizer_factory=lambda phrases: object())
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


def test_driver_overflow_discards_incomplete_audio(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import Mock

    recognizer = Mock()
    calls = []
    worker = None

    def factory(phrases):
        calls.append(phrases)
        if len(calls) == 2:
            worker._stop.set()
        return recognizer

    class Stream:
        def __init__(self, **options):
            self.capture = options["callback"]

        def __enter__(self):
            self.capture(bytes(3200), 1600, None, SimpleNamespace(input_overflow=True))
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr("ergosense.voice.worker.sd.RawInputStream", Stream)
    monkeypatch.setattr("ergosense.voice.worker.stream_options", dict)
    monkeypatch.setattr("ergosense.voice.worker._input_device_name", lambda: "Prueba")
    worker = VoiceWorker(recognizer_factory=factory)
    worker._run()
    assert len(calls) == 2
    recognizer.AcceptWaveform.assert_not_called()
