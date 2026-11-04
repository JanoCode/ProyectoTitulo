"""Pruebas de la ayuda y de los componentes de la interfaz (Sprint 04)."""

from PySide6.QtWidgets import QLabel

from ergosense.ui.help_dialog import GESTURES, GESTURES_TAB, VOICE_TAB, HelpDialog
from ergosense.ui.widgets import StatusIndicator, ToggleSwitch
from ergosense.voice.commands import COMMANDS


def page_text(dialog, tab):
    """Todo el texto visible de una pestaña, en minúsculas."""
    labels = dialog.tabs.widget(tab).findChildren(QLabel)
    return " ".join(label.text() for label in labels).lower()


def test_la_ayuda_abre_en_la_pestana_pedida(qapp):
    dialog = HelpDialog(tab=VOICE_TAB)
    assert dialog.tabs.currentIndex() == VOICE_TAB
    assert dialog.tabs.tabText(VOICE_TAB) == "Comandos de voz"


def test_la_ayuda_muestra_todos_los_comandos_de_voz(qapp):
    # La lista sale del mismo vocabulario del reconocimiento: no puede quedar desfasada.
    text = page_text(HelpDialog(tab=VOICE_TAB), VOICE_TAB)
    for phrase in COMMANDS:
        assert phrase in text


def test_la_ayuda_explica_cada_gesto(qapp):
    text = page_text(HelpDialog(), GESTURES_TAB)
    for gesture, action in GESTURES:
        assert gesture.lower() in text
        assert action.lower() in text


def test_el_interruptor_refleja_el_estado_sin_avisar(qapp):
    toggle = ToggleSwitch()
    changes = []
    toggle.toggled.connect(changes.append)
    toggle.set_checked_silently(True)
    assert toggle.isChecked()
    assert changes == []


def test_el_indicador_cambia_texto_y_estado(qapp):
    indicator = StatusIndicator("Desactivado", "off")
    indicator.set_status("Escuchando", "ok")
    assert indicator.text() == "Escuchando"
    assert indicator.state == "ok"
