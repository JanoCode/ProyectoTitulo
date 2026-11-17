import sys
from pathlib import Path


def portable_model(name):
    if not getattr(sys, "frozen", False):
        return None
    path = Path(sys.executable).parent / "models" / name
    return path if path.is_dir() else None
