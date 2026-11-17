import sys

from ergosense.app.resources import portable_model
from ergosense.voice import dictation, recognizer


def test_portable_models_are_used_without_downloading(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "ErgoSense.exe"))
    for name in [recognizer.MODEL_NAME, dictation.MODEL_FOLDER]:
        (tmp_path / "models" / name).mkdir(parents=True)
    monkeypatch.delenv("ERGOSENSE_VOICE_MODEL", raising=False)
    monkeypatch.delenv("ERGOSENSE_DICTATION_MODEL", raising=False)
    assert recognizer.model_path() == tmp_path / "models" / recognizer.MODEL_NAME
    assert dictation.dictation_model_path() == tmp_path / "models" / dictation.MODEL_FOLDER


def test_explicit_model_overrides_portable(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "ErgoSense.exe"))
    (tmp_path / "models" / dictation.MODEL_FOLDER).mkdir(parents=True)
    monkeypatch.setenv("ERGOSENSE_DICTATION_MODEL", str(tmp_path / "custom"))
    assert dictation.dictation_model_path() == tmp_path / "custom"


def test_source_execution_does_not_use_folders_beside_python(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert portable_model("whisper-small") is None
