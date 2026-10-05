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
