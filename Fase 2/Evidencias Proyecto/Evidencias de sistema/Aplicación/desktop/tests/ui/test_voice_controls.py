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


def test_muestra_el_microfono_que_se_esta_usando(qapp):
    window = MainWindow()
    window.set_voice_enabled(True)
    # Así lo entrega Windows: con prefijo y, a veces, recortado.
    window.show_microphone("Micrófono (2- H510-PRO Wireless")
    assert window.microphone_label.text() == "Micrófono: H510-PRO Wireless"
    assert not window.microphone_label.isHidden()
    window.set_voice_enabled(False)
    assert window.microphone_label.isHidden()
    window.close()


def test_sin_modelo_de_voz_lo_informa(qapp):
    window = MainWindow()
    window.set_voice_enabled(True)
    window.show_voice_status("Falta el modelo de voz")
    assert window.voice_status.text() == "Falta el modelo de voz"
    assert window.voice_status.state == "error"
    window.close()


def test_la_primera_vez_muestra_el_avance_de_la_descarga(qapp):
    window = MainWindow()
    window.set_voice_enabled(True)
    window.show_voice_status("Descargando voz · 45 %")
    assert window.voice_status.text() == "Descargando voz · 45 %"
    assert window.voice_status.state == "waiting"
    assert "Solo la primera vez" in window.microphone_label.text()
    assert not window.microphone_label.isHidden()
    # Al terminar, la ayuda de la descarga se reemplaza por el micrófono.
    window.show_voice_status("Iniciando micrófono...")
    assert window.microphone_label.isHidden()
    window.show_microphone("Mic")
    window.show_voice_status("Activo · micrófono en uso")
    assert window.microphone_label.text() == "Micrófono: Mic"
    assert not window.microphone_label.isHidden()
    window.close()


def test_si_la_descarga_falla_dice_que_hacer(qapp):
    window = MainWindow()
    window.set_voice_enabled(True)
    window.show_voice_status("No se pudo descargar")
    assert window.voice_status.state == "error"
    assert "conexión a internet" in window.microphone_label.text()
    window.close()


def test_el_nombre_del_microfono_se_muestra_limpio(qapp):
    window = MainWindow()
    window.set_voice_enabled(True)
    window.show_microphone("Microphone (Realtek(R) Audio)")
    assert window.microphone_label.text() == "Micrófono: Realtek(R) Audio"
    window.show_microphone("Logitech Webcam")
    assert window.microphone_label.text() == "Micrófono: Logitech Webcam"
    window.close()
