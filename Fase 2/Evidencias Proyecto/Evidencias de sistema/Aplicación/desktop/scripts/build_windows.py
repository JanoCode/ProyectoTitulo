import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

DESKTOP = Path(__file__).resolve().parents[1]


def icon_file(work):
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PIL import Image
    from PySide6.QtWidgets import QApplication

    from ergosense.ui import icons

    app = QApplication([])
    png = work / "ergosense.png"
    icons.pixmap("logo", size=256).save(str(png))
    with Image.open(png) as image:
        image.save(work / "ergosense.ico", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
    app.quit()


def copy_models(destination):
    from huggingface_hub import snapshot_download

    from ergosense.voice.dictation import (
        MODEL_REPOSITORY,
        MODEL_REVISION,
        dictation_model_path,
    )
    from ergosense.voice.recognizer import MODEL_NAME, download_model

    voice = download_model()
    whisper = dictation_model_path()
    required = ("model.bin", "config.json", "tokenizer.json", "vocabulary.txt")
    if not all((whisper / name).is_file() for name in required):
        snapshot_download(
            MODEL_REPOSITORY, revision=MODEL_REVISION, local_dir=whisper,
            allow_patterns=list(required),
        )
    model_folder = destination / "models"
    shutil.copytree(voice, model_folder / MODEL_NAME)
    (model_folder / "whisper-small").mkdir()
    for name in required:
        shutil.copy2(whisper / name, model_folder / "whisper-small" / name)


def licenses(destination):
    folder = destination / "licenses"
    folder.mkdir()
    with urllib.request.urlopen(
        "https://raw.githubusercontent.com/openai/whisper/main/LICENSE", timeout=30,
    ) as response:
        (folder / "Whisper-model-MIT.txt").write_bytes(response.read())
    for dist in importlib.metadata.distributions():
        name = dist.metadata["Name"] or "package"
        for item in dist.files or []:
            if any(part.lower().startswith(("license", "copying", "notice")) for part in item.parts):
                source = Path(dist.locate_file(item))
                if source.is_file():
                    target = folder / name / Path(*item.parts)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    (destination / "DEPENDENCIAS.json").write_text(json.dumps({
        dist.metadata["Name"]: dist.version for dist in importlib.metadata.distributions()
        if dist.metadata["Name"]
    }, indent=2, sort_keys=True), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Construye la versión portable para Windows x64")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if sys.platform != "win32" or platform.machine().upper() not in ("AMD64", "X86_64"):
        parser.error("La compilación requiere Windows x64.")
    output = args.output.resolve()
    if (output / "ErgoSense").exists():
        parser.error("Ya existe una carpeta ErgoSense en el destino. Elige otro destino vacío.")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ergosense-build-") as temporary:
        work = Path(temporary)
        icon_file(work)
        environment = os.environ | {"ERGOSENSE_BUILD_ICON": str(work / "ergosense.ico")}
        subprocess.run([
            sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
            "--distpath", str(output), "--workpath", str(work),
            str(DESKTOP / "packaging/ErgoSense.spec"),
        ], cwd=DESKTOP, env=environment, check=True)
    destination = output / "ErgoSense"
    copy_models(destination)
    licenses(destination)
    shutil.copy2(DESKTOP / "packaging/LEEME.txt", destination / "LEEME.txt")
    report = output / "verificacion-ejecutable.json"
    process = subprocess.run([
        str(destination / "ErgoSense.exe"), "--self-test", str(report),
    ], cwd=output, timeout=180, check=False)
    if process.returncode or not report.is_file() or not json.loads(report.read_text())["ok"]:
        raise RuntimeError("El ejecutable no superó la verificación. Revisa el registro local.")
    archive = Path(shutil.make_archive(str(output / "ErgoSense-Windows-x64"), "zip", output, "ErgoSense"))
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    archive.with_suffix(".zip.sha256").write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    print(f"Ejecutable: {destination / 'ErgoSense.exe'}")
    print(f"Paquete: {archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
