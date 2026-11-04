"""Reconocedor de voz Vosk, sin conexión a internet (PB-14; RNF-17).

El audio se procesa en este equipo: nunca se guarda ni se envía a otro servicio.
El modelo en español (vosk-model-small-es-0.42, licencia Apache 2.0) pesa unos
58 MB, por eso no está en el repositorio: se descarga una vez con
scripts/download_voice_model.py en la carpeta local de la aplicación.
"""

import ctypes
import os
import threading
from pathlib import Path

import vosk

from ergosense.voice.grammar import grammar_json

MODEL_NAME = "vosk-model-small-es-0.42"
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_NAME}.zip"
SAMPLE_RATE = 16000  # el modelo trabaja con audio de 16 kHz, mono


class VoiceModelMissing(Exception):
    """No se encontró el modelo de voz en el equipo."""


def models_folder():
    """Carpeta local de la aplicación, fuera de OneDrive: %LOCALAPPDATA%\\ErgoSense."""
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "ErgoSense" / "models"


def model_path():
    """Dónde está el modelo. ERGOSENSE_VOICE_MODEL permite usar otra carpeta."""
    custom = os.environ.get("ERGOSENSE_VOICE_MODEL")
    return Path(custom) if custom else models_folder() / MODEL_NAME


def _ascii_path(path):
    """Vosk no abre rutas con tildes en Windows; la ruta corta de Windows no las tiene."""
    text = str(path)
    if text.isascii() or os.name != "nt":
        return text
    buffer = ctypes.create_unicode_buffer(1024)
    if ctypes.windll.kernel32.GetShortPathNameW(text, buffer, len(buffer)):
        return buffer.value
    return text


_model = None
_model_lock = threading.Lock()


def load_model():
    """Carga el modelo una sola vez; tarda unos segundos la primera vez."""
    global _model
    with _model_lock:
        if _model is None:
            path = model_path()
            if not (path / "am" / "final.mdl").is_file():
                raise VoiceModelMissing(str(path))
            vosk.SetLogLevel(-1)  # sin mensajes técnicos de Vosk en la consola
            _model = vosk.Model(_ascii_path(path))
        return _model


def create_recognizer():
    """Reconocedor limitado a los comandos y a las palabras de relleno (grammar.py)."""
    return vosk.KaldiRecognizer(load_model(), SAMPLE_RATE, grammar_json())
