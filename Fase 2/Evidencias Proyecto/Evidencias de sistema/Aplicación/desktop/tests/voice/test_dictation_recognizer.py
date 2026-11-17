import json
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np

from ergosense.voice.dictation import FRAME_BYTES, DictationRecognizer


class FrameVad:
    def is_speech(self, frame, sample_rate):
        assert len(frame) == FRAME_BYTES
        assert sample_rate == 16000
        return frame != bytes(FRAME_BYTES)


def recognizer(text="Buscar información sobre ergonomía."):
    model = Mock()
    model.transcribe.return_value = (iter([SimpleNamespace(text=text)]), None)
    return DictationRecognizer(model, FrameVad()), model


def speech(frames=20):
    return b"\x10\x00" * (FRAME_BYTES // 2) * frames


def silence(frames=40):
    return bytes(FRAME_BYTES * frames)


def test_silence_never_runs_transcription():
    rec, model = recognizer()
    assert not rec.AcceptWaveform(silence(300))
    assert json.loads(rec.FinalResult()) == {"text": ""}
    model.transcribe.assert_not_called()


def test_waits_for_silence_then_preserves_accents_and_punctuation():
    rec, model = recognizer()
    states = []
    rec.set_state_callback(states.append)
    assert not rec.AcceptWaveform(speech())
    assert not rec.AcceptWaveform(silence(20))
    assert rec.AcceptWaveform(silence(20))
    assert json.loads(rec.Result())["text"] == "Buscar información sobre ergonomía."
    assert states == ["processing", "listening"]
    kwargs = model.transcribe.call_args.kwargs
    assert kwargs["language"] == "es"
    assert kwargs["task"] == "transcribe"
    assert kwargs["condition_on_previous_text"] is False
    assert kwargs["vad_filter"] is True
    samples = model.transcribe.call_args.args[0]
    assert samples.dtype == np.float32


def test_partial_frames_are_retained_until_complete():
    rec, model = recognizer()
    audio = speech() + silence()
    for position in range(0, len(audio), 173):
        rec.AcceptWaveform(audio[position:position + 173])
    assert json.loads(rec.Result())["text"].startswith("Buscar")
    assert model.transcribe.call_count == 1


def test_short_impulse_is_not_transcribed():
    rec, model = recognizer()
    assert not rec.AcceptWaveform(speech(2) + silence())
    model.transcribe.assert_not_called()


def test_continuous_audio_is_split_at_a_bounded_duration():
    rec, model = recognizer()
    assert rec.AcceptWaveform(speech(610))
    assert model.transcribe.call_count == 1
    assert model.transcribe.call_args.args[0].size <= 16000 * 12


def test_failure_returns_indicator_to_listening_and_propagates():
    import pytest
    rec, model = recognizer()
    model.transcribe.side_effect = RuntimeError("decoder unavailable")
    states = []
    rec.set_state_callback(states.append)
    with pytest.raises(RuntimeError):
        rec.AcceptWaveform(speech() + silence())
    assert states == ["processing", "listening"]
