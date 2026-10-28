from unittest.mock import Mock

from ergosense.app.preferences import PreferencesController


def test_preferences_start_and_stop_voice_without_changing_gestures():
    gestures, inactivity, window, voice = Mock(), Mock(), Mock(), Mock()
    gestures.running = True
    controller = PreferencesController(gestures, inactivity, window, voice=voice)
    settings = {
        "gesture_enabled": True,
        "voice_enabled": True,
        "inactivity_break_minutes": 10,
    }
    controller.apply(settings)
    voice.start.assert_called_once()
    window.set_voice_enabled.assert_called_with(True)
    gestures.stop.assert_not_called()
    settings["voice_enabled"] = False
    controller.apply(settings)
    voice.stop.assert_called_once()
    window.set_voice_enabled.assert_called_with(False)
