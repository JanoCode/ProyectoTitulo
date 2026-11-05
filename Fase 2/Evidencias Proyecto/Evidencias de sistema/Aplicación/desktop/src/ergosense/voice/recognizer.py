"""Reconocedor de voz Vosk, sin conexión a internet (PB-14; RNF-17).

El audio se procesa en este equipo: nunca se guarda ni se envía a otro servicio.
El modelo en español (vosk-model-small-es-0.42, licencia Apache 2.0) pesa unos
40 MB comprimido, por eso no está en el repositorio: ErgoSense lo descarga solo la
primera vez que se activa la voz, en la carpeta local de la aplicación. Esa
descarga es lo único que necesita internet, y no envía nada del usuario.
"""

import ctypes
import hashlib
import os
import shutil
import tempfile
import threading
import urllib.request
import zipfile
from pathlib import Path

import vosk

from ergosense.voice.grammar import grammar_json

MODEL_NAME = "vosk-model-small-es-0.42"
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_NAME}.zip"
# Huella del archivo oficial: si lo descargado no coincide, está dañado o alterado
# y no se instala.
MODEL_SHA256 = "09b239888f633ef2f0b4e09736e3d9936acfd810bc65d53fad45261762c6511f"
SAMPLE_RATE = 16000  # el modelo trabaja con audio de 16 kHz, mono
DOWNLOAD_PREFIX = "descarga-"  # carpeta temporal de una descarga en curso


class VoiceModelMissing(Exception):
    """No se encontró el modelo de voz en el equipo."""


class ModelDownloadError(Exception):
    """No se pudo descargar o instalar el modelo de voz."""


class DownloadCancelled(Exception):
    """Se apagó la voz mientras se descargaba el modelo."""


def models_folder():
    """Carpeta local de la aplicación, fuera de OneDrive: %LOCALAPPDATA%\\ErgoSense."""
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "ErgoSense" / "models"


def model_path():
    """Dónde está el modelo. ERGOSENSE_VOICE_MODEL permite usar otra carpeta."""
    custom = os.environ.get("ERGOSENSE_VOICE_MODEL")
    return Path(custom) if custom else models_folder() / MODEL_NAME


def is_installed(path=None):
    path = model_path() if path is None else path
    return (path / "am" / "final.mdl").is_file()


_download_lock = threading.Lock()


def download_model(progress=None, cancelled=lambda: False):
    """Descarga e instala el modelo, si falta. Devuelve la carpeta del modelo.

    progress recibe el avance, de 0 a 100. Si cancelled() pasa a ser verdadero, la
    descarga se detiene con DownloadCancelled y no queda nada a medias.
    """
    target = model_path()
    # Si la voz se apaga y se vuelve a encender, la segunda descarga espera a la
    # primera en vez de bajar el mismo archivo dos veces al mismo tiempo.
    with _download_lock:
        if is_installed(target):
            return target
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            # Restos de una descarga que se cortó al cerrar la aplicación.
            for old in target.parent.glob(f"{DOWNLOAD_PREFIX}*"):
                shutil.rmtree(old, ignore_errors=True)
            # Se descarga junto al destino: al final basta renombrar la carpeta, y
            # el modelo queda completo o no queda.
            with tempfile.TemporaryDirectory(
                prefix=DOWNLOAD_PREFIX, dir=target.parent
            ) as folder:
                archive = Path(folder) / f"{MODEL_NAME}.zip"
                _fetch(archive, progress, cancelled)
                with zipfile.ZipFile(archive) as zipped:
                    zipped.extractall(folder)
                extracted = Path(folder) / MODEL_NAME
                if not is_installed(extracted):
                    raise ModelDownloadError("El archivo no contiene el modelo de voz.")
                if target.exists():
                    shutil.rmtree(target)  # un modelo anterior incompleto
                extracted.rename(target)
        except (OSError, zipfile.BadZipFile) as error:
            # Sin internet, sin espacio en el disco o un archivo dañado.
            raise ModelDownloadError(str(error)) from error
    return target


def _fetch(archive, progress, cancelled):
    """Baja el archivo por partes, informa el avance y comprueba su huella."""
    digest = hashlib.sha256()
    with (
        urllib.request.urlopen(MODEL_URL, timeout=30) as response,
        archive.open("wb") as file,
    ):
        total = int(response.headers.get("Content-Length") or 0)
        done = 0
        while chunk := response.read(64 * 1024):
            if cancelled():
                raise DownloadCancelled
            file.write(chunk)
            digest.update(chunk)
            done += len(chunk)
            if progress is not None and total:
                progress(min(100, done * 100 // total))
    if digest.hexdigest() != MODEL_SHA256:
        raise ModelDownloadError("El archivo descargado está dañado.")


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
            if not is_installed(path):
                raise VoiceModelMissing(str(path))
            vosk.SetLogLevel(-1)  # sin mensajes técnicos de Vosk en la consola
            _model = vosk.Model(_ascii_path(path))
        return _model


def create_recognizer(macro_phrases=()):
    """Reconocedor limitado a los comandos, las frases de las macros activadas y las
    palabras de relleno (grammar.py).

    Vosk no permite cambiar la gramática de un reconocedor que ya recibió audio
    (SetGrammar cierra la aplicación), por eso, cuando cambian las macros, se crea
    uno nuevo: tarda alrededor de 1 ms, porque el modelo ya está cargado.
    """
    return vosk.KaldiRecognizer(load_model(), SAMPLE_RATE, grammar_json(macro_phrases))
