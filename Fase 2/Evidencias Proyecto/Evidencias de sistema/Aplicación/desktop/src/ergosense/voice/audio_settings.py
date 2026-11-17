import json
import os
from pathlib import Path

import sounddevice as sd


def settings_path():
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData/Local")
    return base / "ErgoSense/audio.json"


def selected_microphone():
    try:
        value = json.loads(settings_path().read_text(encoding="utf-8"))
        if isinstance(value, dict) and isinstance(value.get("name"), str) and isinstance(value.get("hostapi"), str):
            return value
    except (OSError, ValueError, TypeError):
        pass
    return None


def input_devices():
    try:
        devices = sd.query_devices()
        hosts = sd.query_hostapis()
    except (sd.PortAudioError, OSError):
        return []
    candidates = [(index, device, hosts[device["hostapi"]]["name"])
                  for index, device in enumerate(devices) if device["max_input_channels"] > 0]
    wasapi = [entry for entry in candidates if entry[2] == "Windows WASAPI"]
    return wasapi or candidates


def save_microphone(choice):
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(choice, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def stream_options():
    choice = selected_microphone()
    if choice is None:
        return {}
    for index, device, host in input_devices():
        if device["name"] == choice["name"] and host == choice["hostapi"]:
            options = {"device": index}
            if host == "Windows WASAPI":
                options["extra_settings"] = sd.WasapiSettings(auto_convert=True)
            return options
    raise ValueError("El micrófono seleccionado no está conectado.")
