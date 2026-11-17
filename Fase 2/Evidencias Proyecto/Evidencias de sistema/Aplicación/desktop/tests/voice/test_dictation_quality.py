import json
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np

from ergosense.voice.dictation import DictationRecognizer


class SpeechVad:
    def is_speech(self, frame, rate):
        return any(frame)


def audio(amplitude=.003, seconds=.5):
    samples = np.sin(np.arange(int(16000 * seconds)) * 2 * np.pi * 440 / 16000) * amplitude
    return (samples * 32767).astype(np.int16).tobytes()


def test_low_level_audio_is_boosted_without_clipping_and_warns_once():
    model = Mock()
    model.transcribe.side_effect = lambda *a, **k: (iter([SimpleNamespace(text="Prueba")]), None)
    rec = DictationRecognizer(model, SpeechVad())
    notices = []
    rec.set_quality_callback(notices.append)
    for _ in range(2):
        rec.AcceptWaveform(audio() + bytes(16000 * 2))
        assert json.loads(rec.Result())["text"] == "Prueba"
    samples = model.transcribe.call_args.args[0]
    assert np.max(np.abs(samples)) > .01
    assert np.max(np.abs(samples)) <= .95
    assert len(notices) == 1


def test_constant_offset_is_not_transcribed_as_voice():
    model = Mock()
    rec = DictationRecognizer(model, SpeechVad())
    rec.AcceptWaveform(np.full(8000, 4000, dtype=np.int16).tobytes())
    assert json.loads(rec.FinalResult()) == {"text": ""}
    model.transcribe.assert_not_called()


def test_clipped_audio_reports_input_problem():
    model = Mock()
    model.transcribe.return_value = (iter([]), None)
    rec = DictationRecognizer(model, SpeechVad())
    notices = []
    rec.set_quality_callback(notices.append)
    clipped = np.tile(np.array([32767, -32768], dtype=np.int16), 4000)
    rec.AcceptWaveform(clipped.tobytes() + bytes(16000 * 2))
    assert any("saturando" in message for message in notices)


def test_cuda_failure_falls_back_to_cpu(monkeypatch, tmp_path):
    from ergosense.voice import dictation

    for name in dictation.MODEL_FILES:
        (tmp_path / name).touch()
    factory = Mock(side_effect=[RuntimeError("CUDA unavailable"), Mock()])
    monkeypatch.setattr("faster_whisper.WhisperModel", factory)
    monkeypatch.setattr(dictation, "_model", None)
    monkeypatch.setattr(dictation, "dictation_model_path", lambda: tmp_path)
    monkeypatch.setattr(dictation, "cuda_available", lambda: True)
    monkeypatch.delenv("ERGOSENSE_DICTATION_DEVICE", raising=False)
    dictation.load_dictation_model()
    assert factory.call_args_list[0].kwargs["device"] == "cuda"
    assert factory.call_args_list[1].kwargs["device"] == "cpu"


def test_custom_model_is_not_overwritten_by_a_download(monkeypatch, tmp_path):
    import pytest

    from ergosense.voice import dictation

    download = Mock()
    monkeypatch.setattr("huggingface_hub.snapshot_download", download)
    monkeypatch.setattr(dictation, "_model", None)
    monkeypatch.setenv("ERGOSENSE_DICTATION_MODEL", str(tmp_path))
    with pytest.raises(RuntimeError, match="incompleta"):
        dictation.load_dictation_model()
    download.assert_not_called()
