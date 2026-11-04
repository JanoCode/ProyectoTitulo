"""Pruebas de los controles de voz de la ventana principal (Sprint 04)."""

from ergosense.ui.main_window import MainWindow


def test_los_interruptores_piden_cambios_independientes(qapp):
    window = MainWindow()
    requests = []
    window.feature_requested.connect(lambda key, value: requests.append((key, value)))
    window.voice_toggle.click()
    window.gesture_toggle.click()
    assert requests == [("voice_enabled", True), ("gesture_enabled", True)]
    window.set_voice_enabled(True)
    window.show_gestures_starting()
    window.voice_toggle.click()
    window.gesture_toggle.click()
    assert requests[-2:] == [("voice_enabled", False), ("gesture_enabled", False)]
    window.close()


def test_escuchando_muestra_el_microfono_en_uso(qapp):
    window = MainWindow()
    window.set_voice_enabled(True)
    window.show_voice_status("Activo · micrófono en uso")
    assert window.voice_status.text() == "Escuchando"
    assert not window.mic_indicator.isHidden()
    window.close()


def test_la_voz_desactivada_ignora_un_estado_atrasado(qapp):
    window = MainWindow()
    window.set_voice_enabled(True)
    window.show_voice_status("Activo · micrófono en uso")
    window.set_voice_enabled(False)
    window.show_voice_status("Activo · micrófono en uso")
    assert window.voice_status.text() == "Desactivado"
    assert window.mic_indicator.isHidden()
    window.close()


def test_sin_microfono_lo_informa(qapp):
    window = MainWindow()
    window.set_voice_enabled(True)
    window.show_voice_status("Micrófono no disponible")
    assert window.voice_status.text() == "Micrófono no disponible"
    assert window.voice_status.state == "error"
    window.close()
