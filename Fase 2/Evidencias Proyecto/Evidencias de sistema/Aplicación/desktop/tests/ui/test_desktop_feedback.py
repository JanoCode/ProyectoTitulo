from PySide6.QtCore import Qt

from ergosense.ui.desktop_feedback import DesktopFeedback
from ergosense.ui.main_window import MainWindow


def test_modes_are_visible_outside_main_window_and_do_not_accept_focus(qapp):
    feedback = DesktopFeedback()
    feedback.set_features({"gesture_enabled": True, "voice_enabled": True})
    assert feedback.indicator.isVisible()
    assert feedback.indicator.parent() is None
    for flag in (Qt.WindowType.WindowStaysOnTopHint,
                 Qt.WindowType.WindowTransparentForInput,
                 Qt.WindowType.WindowDoesNotAcceptFocus):
        assert feedback.indicator.windowFlags() & flag
        assert feedback.notice.windowFlags() & flag
    feedback.camera_available()
    feedback.hand_changed(True)
    assert "Mano detectada" in feedback.indicator.items[0][1]
    feedback.close()


def test_dictation_announces_readiness_once_and_ignores_late_results(qapp):
    feedback = DesktopFeedback()
    feedback.set_features({"gesture_enabled": False, "voice_enabled": True})
    feedback.set_dictation(True)
    assert feedback.notice.text == "Preparando dictado…"
    feedback.set_dictation_state("listening")
    assert "Dictado activo" in feedback.notice.text
    feedback.set_dictation_state("processing")
    assert feedback.indicator.items[0][1] == "Dictado · Procesando"
    feedback.notify("Otra notificación")
    feedback.set_dictation_state("listening")
    assert feedback.notice.text == "Otra notificación"
    feedback.set_dictation(False)
    feedback.set_dictation_state("processing")
    assert "Dictado" not in feedback.indicator.items[0][1]
    assert feedback.notice.text == "Dictado desactivado."
    feedback.close()


def test_disable_hides_modes_but_keeps_confirmation_then_closes(qapp):
    feedback = DesktopFeedback()
    feedback.set_features({"gesture_enabled": True, "voice_enabled": True})
    feedback.set_features({"gesture_enabled": False, "voice_enabled": False})
    feedback.notify("Gestos y voz desactivados.")
    assert not feedback.indicator.isVisible()
    assert feedback.notice.isVisible()
    feedback.close()
    feedback.notify("Mensaje tardío")
    assert not feedback.notice.isVisible()
    assert not feedback.notice.timer.isActive()


def test_microphone_failure_is_visible_and_does_not_claim_listening(qapp):
    feedback = DesktopFeedback()
    feedback.set_features({"gesture_enabled": False, "voice_enabled": True})
    feedback.voice_status("Micrófono no disponible")
    assert feedback.indicator.items[0][1] == "Voz · No disponible"
    assert feedback.notice.kind == "error"
    feedback.close()


def test_notices_expire_and_new_notice_restarts_timer(qapp):
    feedback = DesktopFeedback()
    feedback.notify("Aviso")
    feedback.notice.timer.timeout.emit()
    assert not feedback.notice.isVisible()
    feedback.notify("Error", "error")
    assert feedback.notice.isVisible()
    assert feedback.notice.timer.interval() == 6000
    feedback.close()


def test_window_routes_messages_to_desktop_overlay_when_minimized(qapp):
    window = MainWindow()
    feedback = DesktopFeedback()
    window.notification_requested.connect(feedback.notify)
    window.showMinimized()
    window.show_toast("Control por gestos activado.")
    assert feedback.notice.isVisible()
    assert feedback.notice.text == "Control por gestos activado."
    feedback.close()
    window.close()
