import pytest

from ergosense.voice import audio_settings


@pytest.fixture
def audio_file(monkeypatch, tmp_path):
    path = tmp_path / "audio.json"
    monkeypatch.setattr(audio_settings, "settings_path", lambda: path)
    return path


def test_microphone_is_persisted_by_name_and_backend_not_unstable_index(audio_file, monkeypatch):
    choice = {"name": "Micrófono USB", "hostapi": "Windows WASAPI"}
    audio_settings.save_microphone(choice)
    monkeypatch.setattr(audio_settings, "input_devices", lambda: [(7, {"name": choice["name"]}, choice["hostapi"])])
    options = audio_settings.stream_options()
    assert options["device"] == 7
    assert options["extra_settings"] is not None


def test_missing_selected_microphone_does_not_silently_capture_another(audio_file, monkeypatch):
    audio_settings.save_microphone({"name": "Desconectado", "hostapi": "Windows WASAPI"})
    monkeypatch.setattr(audio_settings, "input_devices", list)
    with pytest.raises(ValueError, match="no está conectado"):
        audio_settings.stream_options()


@pytest.mark.parametrize("data", ["bad", "[]", '{"name": 2}', 'null'])
def test_invalid_preferences_keep_windows_default(audio_file, data):
    audio_file.write_text(data, encoding="utf-8")
    assert audio_settings.stream_options() == {}
