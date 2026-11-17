import logging
import multiprocessing
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def run():
    multiprocessing.freeze_support()
    with open(os.devnull, "w", encoding="utf-8") as sink:
        if sys.stdout is None:
            sys.stdout = sink
        if sys.stderr is None:
            sys.stderr = sink
        return launch()


def launch():
    folder = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ErgoSense/logs"
    folder.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        handlers=[RotatingFileHandler(
            folder / "desktop.log", maxBytes=2_000_000, backupCount=2, encoding="utf-8",
        )],
        level=logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "--self-test":
            from ergosense.app.portable_check import check

            return check(Path(sys.argv[2]))
        from ergosense.app.main import main

        return main()
    except Exception:
        logging.getLogger("ergosense").exception("No se pudo iniciar ErgoSense")
        if len(sys.argv) == 3 and sys.argv[1] == "--self-test":
            import json

            Path(sys.argv[2]).write_text(json.dumps({"ok": False}), encoding="utf-8")
        else:
            from PySide6.QtWidgets import QApplication, QMessageBox

            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(
                None, "ErgoSense",
                "No se pudo iniciar la aplicación. Extrae la carpeta completa y vuelve "
                f"a intentarlo. El registro del error está en {folder / 'desktop.log'}.",
            )
            del app
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
