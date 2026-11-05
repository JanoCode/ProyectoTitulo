"""Descarga el modelo de voz en español de Vosk (unos 40 MB) por adelantado.

No es obligatorio: ErgoSense lo descarga solo la primera vez que se activa la voz.
Sirve para dejarlo listo antes, por ejemplo en un equipo que después estará sin
internet. Lo guarda en %LOCALAPPDATA%\\ErgoSense\\models, fuera de OneDrive y del
repositorio. Uso, desde la carpeta desktop:
uv run python scripts/download_voice_model.py
"""

from ergosense.voice.recognizer import (
    MODEL_NAME,
    MODEL_URL,
    ModelDownloadError,
    download_model,
    is_installed,
    model_path,
)


def show_progress(percent):
    print(f"\r  Descargando... {percent} %", end="", flush=True)


def main():
    target = model_path()
    if is_installed(target):
        print(f"El modelo ya está instalado en {target}")
        return
    print(f"Descargando {MODEL_NAME} desde {MODEL_URL}")
    try:
        download_model(progress=show_progress)
    except ModelDownloadError as error:
        print(f"\nNo se pudo descargar el modelo: {error}")
        raise SystemExit(1) from error
    print(f"\nListo. El modelo quedó en {target}")


if __name__ == "__main__":
    main()
