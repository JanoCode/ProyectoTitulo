import argparse
import json
import time
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QTimer

from ergosense.actions.executor import ActionExecutor
from ergosense.gestures.camera import Camera
from ergosense.gestures.hand_tracker import HandTracker
from ergosense.gestures.pipeline import GesturePipeline
from ergosense.gestures.worker import GestureWorker
from ergosense.monitoring.activity_period import ActivityPeriod
from ergosense.voice.recognizer import is_installed
from ergosense.voice.worker import VoiceWorker


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=60)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.seconds < 1:
        parser.error("La duración debe ser positiva")
    if not is_installed():
        parser.error("Instala el modelo con scripts/download_voice_model.py")
    app = QCoreApplication([])
    metrics = {"duration_requested_seconds": args.seconds, "frames": 0,
               "hand_frames": 0, "voice_results": 0, "actions_observed": 0,
               "camera_errors": 0, "voice_statuses": [], "timer_alerts": [],
               "os_actions_executed": False, "media_saved": False}
    start = time.monotonic()
    period = ActivityPeriod(time.monotonic)
    period.start()

    def action(value):
        metrics["actions_observed"] += 1

    executor = ActionExecutor(action)
    executor.start()

    class Mouse:
        def move(self, position):
            pass

    gestures = GestureWorker(Camera(), HandTracker,
        GesturePipeline((0, 0, 1920, 1080), time.monotonic), Mouse(), executor)
    voice = VoiceWorker()

    def frame_ready(image, points):
        metrics["frames"] += 1
        metrics["hand_frames"] += points is not None

    def camera_error():
        metrics["camera_errors"] += 1

    def voice_result(text):
        metrics["voice_results"] += 1

    def voice_status(status):
        if not metrics["voice_statuses"] or metrics["voice_statuses"][-1] != status:
            metrics["voice_statuses"].append(status)

    def tick():
        if period.check():
            metrics["timer_alerts"].append(round(time.monotonic() - start, 3))
        if time.monotonic() - start >= args.seconds:
            app.quit()

    gestures.frame_ready.connect(frame_ready)
    gestures.camera_unavailable.connect(camera_error)
    voice.recognized.connect(voice_result)
    voice.status_changed.connect(voice_status)
    timer = QTimer()
    timer.timeout.connect(tick)
    timer.start(100)
    try:
        gestures.start()
        voice.start()
        app.exec()
    finally:
        metrics["camera_running_at_end"] = gestures.running
        metrics["voice_running_at_end"] = voice.running
        gestures.stop()
        voice.stop()
        executor.stop()
    metrics["elapsed_seconds"] = round(time.monotonic() - start, 3)
    metrics["passed_device_smoke"] = (
        metrics["frames"] > 0 and metrics["camera_errors"] == 0
        and metrics["camera_running_at_end"] and metrics["voice_running_at_end"]
        and any("micrófono en uso" in status for status in metrics["voice_statuses"])
    )
    metrics["real_timer_passed"] = (
        3600 <= metrics["timer_alerts"][0] <= 3602
        if args.seconds >= 3601 and metrics["timer_alerts"] else None
    )
    if args.output:
        args.output.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False))
    return 0 if metrics["passed_device_smoke"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
