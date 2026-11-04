"""Pruebas de la ventana principal (Sprints 01, 03 y 04)."""

from PySide6.QtGui import QImage

from ergosense.ui.main_window import MainWindow


class FakeTray:
    """Bandeja falsa: guarda las notificaciones en vez de mostrarlas."""

    def __init__(self):
        self.messages = []

    def showMessage(self, title, message):
        self.messages.append((title, message))


def make_frame():
    image = QImage(64, 48, QImage.Format.Format_RGB888)
    image.fill(0)
    return image


def test_la_ventana_se_llama_ergosense(qapp):
    window = MainWindow()
    assert window.windowTitle() == "ErgoSense"


def test_al_abrir_no_hay_datos(qapp):
    window = MainWindow()
    assert window.period_label.text() == "--:--:--"
    assert window.activity_label.text() == "Sin actividad aún"


def test_cp_01_01_muestra_el_tiempo_del_periodo(qapp):
    window = MainWindow()
    window.show_period(125)
    assert window.period_label.text() == "00:02:05"


def test_muestra_hace_cuanto_fue_la_ultima_actividad(qapp):
    window = MainWindow()
    window.show_last_activity(12)
    assert window.activity_label.text() == "hace 12 segundos"


def test_muestra_la_cuenta_con_sus_iniciales(qapp):
    window = MainWindow()
    window.show_user("Lucía Martínez", "lucia@ejemplo.com")
    assert window.user_name_label.text() == "Lucía Martínez"
    assert window.avatar.text() == "LM"
    assert window.menu_email_label.text() == "lucia@ejemplo.com"


def test_cerrar_sesion_desde_el_menu_de_la_cuenta(qapp):
    window = MainWindow()
    requests = []
    window.logout_requested.connect(lambda: requests.append(True))
    window.logout_action.trigger()
    assert requests == [True]


def test_el_boton_de_configuracion_pide_abrirla(qapp):
    window = MainWindow()
    requests = []
    window.settings_requested.connect(lambda: requests.append(True))
    window.settings_button.click()
    assert requests == [True]


# --- Aviso de pausa (PB-05)


def test_cp_01_07_el_aviso_recomienda_una_pausa(qapp):
    window = MainWindow()
    window.show_alert()
    assert window.pause_dialog.isVisible()
    assert "60 minutos" in window.pause_dialog.message_label.text()
    assert "pausa" in window.pause_dialog.title_label.text()
    window.pause_dialog.close()


def test_cp_01_09_en_segundo_plano_avisa_por_la_bandeja(qapp):
    tray = FakeTray()
    window = MainWindow(tray)  # no se ha mostrado, así que está en segundo plano
    window.show_alert()
    assert len(tray.messages) == 1
    window.pause_dialog.close()


# --- Cámara y control con la mano (PB-07 a PB-13, PB-17)


def test_al_abrir_la_camara_esta_apagada(qapp):
    window = MainWindow()
    assert window.camera_stack.currentWidget() is window.placeholder
    assert window.placeholder.title.text() == "La cámara está apagada"
    assert window.camera_indicator.isHidden()


def test_el_boton_de_la_vista_previa_pide_encender_la_camara(qapp):
    window = MainWindow()
    requests = []
    window.camera_requested.connect(requests.append)
    window.placeholder.action.click()
    assert requests == [True]


def test_cp_04_al_llegar_la_imagen_se_muestra_y_se_indica_la_camara_en_uso(qapp):
    window = MainWindow()
    window.show_camera_starting()
    window.show_frame(make_frame(), None)
    assert window.camera_stack.currentWidget() is window.camera_view
    assert window.camera_view.has_frame()
    assert not window.camera_indicator.isHidden()


def test_una_imagen_atrasada_no_vuelve_a_encender_la_vista(qapp):
    window = MainWindow()
    window.show_camera_starting()
    window.show_camera_off()
    window.show_frame(make_frame(), None)  # llegó después de apagar la cámara
    assert window.camera_stack.currentWidget() is window.placeholder


def test_al_activar_los_gestos_busca_la_mano(qapp):
    window = MainWindow()
    window.show_gestures_starting()
    assert window.gesture_toggle.isChecked()
    assert window.gesture_status.text() == "Buscando tu mano"
    window.show_hand(True)
    assert window.gesture_status.text() == "Mano detectada"


def test_muestra_el_gesto_reconocido_en_castellano(qapp):
    window = MainWindow()
    window.show_gestures_starting()
    window.show_gesture("thumb_in")
    assert window.camera_view.gesture_text == "Gesto detectado: clic izquierdo"


def test_al_activar_los_gestos_aparece_el_gesto_que_ya_se_hacia(qapp):
    window = MainWindow()
    window.show_gesture("point")  # con la vista previa, antes de activar los gestos
    assert window.camera_view.gesture_text == ""
    window.show_gestures_starting()
    assert window.camera_view.gesture_text == "Gesto detectado: mover el cursor"


def test_el_interruptor_pide_activar_o_desactivar_los_gestos(qapp):
    window = MainWindow()
    requests = []
    window.feature_requested.connect(lambda key, value: requests.append((key, value)))
    window.gesture_toggle.click()
    assert requests == [("gesture_enabled", True)]


def test_cp_03_02_informa_que_no_hay_camara(qapp):
    window = MainWindow()
    window.show_gestures_starting()
    window.show_camera_unavailable()
    assert "cámara" in window.placeholder.title.text()
    assert window.gesture_status.text() == "Cámara no disponible"


def test_al_reintentar_la_camara_vuelve_a_buscar_la_mano(qapp):
    window = MainWindow()
    window.show_gestures_starting()
    window.show_hand(True)
    window.show_camera_unavailable()
    window.show_camera_starting()  # el usuario pulsó «Reintentar»
    assert window.gesture_status.text() == "Buscando tu mano"
    window.show_hand(True)  # llegan imágenes y se ve la mano
    assert window.gesture_status.text() == "Mano detectada"


def test_cp_03_12_una_senal_atrasada_no_muestra_activos_los_gestos_desactivados(qapp):
    window = MainWindow()
    window.show_gestures_starting()
    window.show_gestures_disabled()
    window.show_gesture("point")  # llegó tarde, desde el hilo que ya se detuvo
    window.show_hand(True)
    assert window.gesture_status.text() == "Desactivado"
    assert window.camera_view.gesture_text == ""


# --- Conexión y mensajes


def test_indica_si_no_hay_conexion_con_el_servidor(qapp):
    window = MainWindow()
    window.show_connection(False)
    assert window.connection_label.text() == "Sin conexión con el servidor"
    window.show_connection(True)
    assert window.connection_label.text() == "Conectado"


def test_muestra_un_mensaje_breve(qapp):
    window = MainWindow()
    window.show_toast("Preferencias guardadas.")
    assert window.toast.text_label.text() == "Preferencias guardadas."
