import argparse
import ctypes
import json
import os
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from ergosense.ui.desktop_feedback import DesktopFeedback


def main():
    parser = argparse.ArgumentParser(description="Verifica los avisos nativos de Windows")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("La comprobación requiere Windows.")
    app = QApplication([])
    user32 = ctypes.windll.user32
    user32.GetForegroundWindow.restype = ctypes.c_void_p
    user32.GetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int]
    user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    foreground = user32.GetForegroundWindow()
    feedback = DesktopFeedback()
    feedback.set_features({"gesture_enabled": True, "voice_enabled": True})
    feedback.camera_available()
    feedback.hand_changed(True)
    feedback.set_dictation(True)
    feedback.set_dictation_state("listening")
    app.processEvents()
    result = {"focus_preserved": foreground == user32.GetForegroundWindow()}
    for name, panel in [("indicator", feedback.indicator), ("notice", feedback.notice)]:
        style = user32.GetWindowLongPtrW(int(panel.winId()), -20)
        result[name] = {
            "topmost": bool(style & 0x8), "click_through": bool(style & 0x20),
            "no_activate": bool(style & 0x08000000), "visible": panel.isVisible(),
        }
        panel.grab().save(str(args.output.with_name(name + ".png")))

    def finish():
        feedback.close()
        result["closed"] = not feedback.indicator.isVisible() and not feedback.notice.isVisible()
        result["ok"] = result["focus_preserved"] and result["closed"] and all(
            all(result[name].values()) for name in ("indicator", "notice")
        )
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        app.quit()

    QTimer.singleShot(1000, finish)
    app.exec()
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
