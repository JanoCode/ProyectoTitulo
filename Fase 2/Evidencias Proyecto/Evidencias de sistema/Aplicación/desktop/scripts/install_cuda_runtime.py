import importlib.metadata
import json
import os
import shutil
from pathlib import Path


def main():
    if os.name != "nt":
        raise SystemExit("Esta preparación del ejecutable requiere Windows.")
    target = Path(os.environ["LOCALAPPDATA"]) / "ErgoSense/cuda/bin"
    target.mkdir(parents=True, exist_ok=True)
    versions = {}
    for name in ("nvidia-cublas-cu12", "nvidia-cuda-runtime-cu12", "nvidia-cuda-nvrtc-cu12"):
        distribution = importlib.metadata.distribution(name)
        versions[name] = distribution.version
        for file in distribution.files or []:
            source = Path(distribution.locate_file(file))
            if source.suffix.lower() == ".dll":
                shutil.copy2(source, target / source.name)
            elif "license" in source.name.lower() and source.is_file():
                destination = target / "licenses" / name / source.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
    (target / "versions.json").write_text(json.dumps(versions, indent=2), encoding="utf-8")
    print(f"Bibliotecas de aceleración preparadas en {target}")


if __name__ == "__main__":
    main()
