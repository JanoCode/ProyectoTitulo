"""Descarga el modelo de voz en español de Vosk (unos 40 MB) una sola vez.

Lo guarda en %LOCALAPPDATA%\\ErgoSense\\models, fuera de OneDrive y del repositorio.
Uso, desde la carpeta desktop: uv run python scripts/download_voice_model.py
"""

import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from ergosense.voice.recognizer import MODEL_NAME, MODEL_URL, model_path


def show_progress(blocks, block_size, total):
    if total > 0:
        percent = min(100, blocks * block_size * 100 // total)
        print(f"\r  Descargando... {percent} %", end="", flush=True)


def main():
    target = model_path()
    if (target / "am" / "final.mdl").is_file():
        print(f"El modelo ya está instalado en {target}")
        return
    print(f"Descargando {MODEL_NAME} desde {MODEL_URL}")
    with tempfile.TemporaryDirectory() as folder:
        archive = Path(folder) / f"{MODEL_NAME}.zip"
        urllib.request.urlretrieve(MODEL_URL, archive, show_progress)
        print("\n  Descomprimiendo...")
        with zipfile.ZipFile(archive) as zipped:
            zipped.extractall(folder)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            shutil.rmtree(target)  # una descarga anterior que quedó incompleta
        shutil.move(str(Path(folder) / MODEL_NAME), target)
    print(f"Listo. El modelo quedó en {target}")


if __name__ == "__main__":
    main()
