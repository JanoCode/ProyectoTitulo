import os
from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    copy_metadata,
)

desktop = Path(SPECPATH).parent
datas = [(str(desktop / "src/ergosense/gestures/models/hand_landmarker.task"),
          "ergosense/gestures/models")]
binaries = []
for package in ("mediapipe", "vosk", "ctranslate2", "faster_whisper"):
    datas += collect_data_files(package)
    binaries += collect_dynamic_libs(package)
for package in ("keyring", "faster-whisper", "huggingface-hub", "mediapipe", "vosk"):
    datas += copy_metadata(package)

analysis = Analysis(
    [str(desktop / "packaging/launcher.py")],
    pathex=[str(desktop / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        "pynput.keyboard._win32", "pynput.mouse._win32", "keyring.backends.Windows",
        "win32ctypes.core.ctypes", "win32ctypes.pywin32",
    ],
    excludes=["pytest", "PyQt5", "PyQt6", "PySide2", "tkinter", "IPython"],
    noarchive=False,
)
analysis.binaries = [
    item for item in analysis.binaries
    if Path(item[0]).name.lower() not in {"icuuc.dll", "icuin.dll"}
    and not Path(item[0]).name.lower().startswith("icudt")
]
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz, analysis.scripts, [], exclude_binaries=True, name="ErgoSense",
    console=False, debug=False, strip=False, upx=False,
    icon=os.environ["ERGOSENSE_BUILD_ICON"],
)
distribution = COLLECT(
    exe, analysis.binaries, analysis.datas, strip=False, upx=False, name="ErgoSense",
)
