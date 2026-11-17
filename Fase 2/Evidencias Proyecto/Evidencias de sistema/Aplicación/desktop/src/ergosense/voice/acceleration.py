import ctypes
import os
import sys
from pathlib import Path

_dll_directories = []


def cuda_available():
    import ctranslate2

    if os.name == "nt":
        bundled = Path(getattr(sys, "_MEIPASS", sys.prefix))
        site = Path(sys.prefix) / "Lib/site-packages"
        local = Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
        folders = [
            root / "nvidia" / package / "bin"
            for root in (bundled, site)
            for package in ("cublas", "cuda_runtime", "cuda_nvrtc")
        ] + [local / "ErgoSense/cuda/bin"]
        for folder in folders:
            if folder.is_dir():
                _dll_directories.append(os.add_dll_directory(str(folder)))
        try:
            ctypes.WinDLL("cublas64_12.dll")
        except OSError:
            return False
    try:
        return ctranslate2.get_cuda_device_count() > 0
    except (RuntimeError, OSError):
        return False
