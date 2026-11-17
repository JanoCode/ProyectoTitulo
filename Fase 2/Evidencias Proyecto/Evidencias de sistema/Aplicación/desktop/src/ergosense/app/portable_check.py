import json
import os


def check(output):
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    import keyring
    import numpy as np
    import sounddevice
    import webrtcvad
    from PySide6.QtWidgets import QApplication

    from ergosense.api_client import ApiClient
    from ergosense.app.main import main
    from ergosense.gestures.hand_tracker import HandTracker
    from ergosense.ui import icons
    from ergosense.ui.auth_dialogs import LoginDialog
    from ergosense.ui.desktop_feedback import DesktopFeedback
    from ergosense.ui.theme import apply_theme
    from ergosense.voice.dictation import load_dictation_model
    from ergosense.voice.recognizer import create_recognizer

    app = QApplication([])
    assert callable(main)
    apply_theme(app)
    assert not icons.app_icon().isNull()
    client = ApiClient("http://127.0.0.1:8000/api/v1")
    window = LoginDialog(client)
    window.show()
    app.processEvents()
    assert window.isVisible()
    window.close()
    client.close()
    feedback = DesktopFeedback()
    feedback.set_features({"gesture_enabled": True, "voice_enabled": True})
    feedback.set_dictation(True)
    feedback.set_dictation_state("listening")
    app.processEvents()
    assert feedback.indicator.isVisible() and feedback.notice.isVisible()
    feedback.close()
    tracker = HandTracker()
    assert tracker.detect(np.zeros((480, 640, 3), dtype=np.uint8)) is None
    tracker.close()
    voice = create_recognizer()
    voice.AcceptWaveform(bytes(3200))
    assert isinstance(voice.Result(), str)
    vad = webrtcvad.Vad(2)
    assert not vad.is_speech(bytes(640), 16000)
    model = load_dictation_model()
    segments, _ = model.transcribe(np.zeros(16000, dtype=np.float32), language="es")
    list(segments)
    backend = type(keyring.get_keyring()).__name__
    assert backend != "Keyring" or "fail" not in type(keyring.get_keyring()).__module__
    try:
        audio_devices = len(sounddevice.query_devices())
    except sounddevice.PortAudioError:
        audio_devices = None
    output.write_text(json.dumps({
        "ok": True, "qt": True, "hand_tracking": True, "vosk": True,
        "dictation": True, "vad": True, "desktop_feedback": True,
        "credential_backend": backend,
        "audio_devices": audio_devices,
    }, indent=2), encoding="utf-8")
    return 0
