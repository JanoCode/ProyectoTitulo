from ergosense.ui.main_window import MainWindow


def test_buttons_request_independent_feature_changes(qapp):
    window = MainWindow()
    requests = []
    window.feature_requested.connect(lambda key, value: requests.append((key, value)))
    window.voice_button.click()
    window.gesture_button.click()
    assert requests == [("voice_enabled", True), ("gesture_enabled", True)]
    window.set_voice_enabled(True)
    window.show_gestures_starting()
    window.voice_button.click()
    window.gesture_button.click()
    assert requests[-2:] == [("voice_enabled", False), ("gesture_enabled", False)]
    window.close()


def test_disabled_voice_ignores_late_status(qapp):
    window = MainWindow()
    window.set_voice_enabled(True)
    window.show_voice_status("Activo · micrófono en uso")
    assert "micrófono" in window.voice_label.text()
    window.set_voice_enabled(False)
    window.show_voice_status("Activo · micrófono en uso")
    assert window.voice_label.text() == "Desactivado"
    window.close()
