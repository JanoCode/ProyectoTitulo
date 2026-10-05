"""Pruebas de la ventana principal (Sprint 01)."""

from ergosense.ui.main_window import MainWindow


def test_la_ventana_se_llama_ergosense(qapp):
    window = MainWindow()
    assert window.windowTitle() == "ErgoSense"


def test_al_abrir_no_hay_datos(qapp):
    window = MainWindow()
    assert window.period_label.text() == "--:--:--"
    assert window.activity_label.text() == "--:--:--"


def test_cp_01_01_muestra_el_tiempo_del_periodo(qapp):
    window = MainWindow()
    window.show_period(125)
    assert window.period_label.text() == "00:02:05"


def test_muestra_el_tiempo_desde_la_ultima_actividad(qapp):
    window = MainWindow()
    window.show_last_activity(7)
    assert window.activity_label.text() == "00:00:07"


def test_sin_actividad_muestra_guiones(qapp):
    window = MainWindow()
    window.show_last_activity(7)
    window.show_last_activity(None)
    assert window.activity_label.text() == "--:--:--"


class FakeTray:
    """Bandeja falsa: guarda las notificaciones en vez de mostrarlas."""

    def __init__(self):
        self.messages = []

    def showMessage(self, title, message):
        self.messages.append((title, message))


def test_al_abrir_no_hay_aviso(qapp):
    window = MainWindow()
    assert window.alert_label.text() == ""


def test_cp_01_07_el_aviso_recomienda_una_pausa(qapp):
    window = MainWindow()
    window.show_alert()
    assert "60 minutos" in window.alert_label.text()
    assert "pausa" in window.alert_label.text()


def test_cp_01_09_en_segundo_plano_avisa_por_la_bandeja(qapp):
    tray = FakeTray()
    window = MainWindow(tray)  # no se ha mostrado, así que está en segundo plano
    window.show_alert()
    assert len(tray.messages) == 1
