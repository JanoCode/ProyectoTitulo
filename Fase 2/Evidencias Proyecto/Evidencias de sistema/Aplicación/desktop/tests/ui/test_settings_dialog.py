"""Pruebas de la configuración del registro de pausas (PB-36 y PB-37)."""

from ergosense.api_client import ApiClientError
from ergosense.ui.settings_dialog import MAX_MINUTES, SettingsDialog


class FakeApiClient:
    """Cliente falso: guarda lo que se le envía, o falla si se le indica."""

    def __init__(self, error=None):
        self.settings = {
            "inactivity_break_minutes": 10,
            "voice_enabled": True,
            "gesture_enabled": True,
        }
        self.error = error
        self.sent = None

    def update_settings(self, changes):
        if self.error:
            raise self.error
        self.sent = changes
        self.settings = {**self.settings, **changes}
        return self.settings


def test_muestra_la_configuracion_actual(qapp):
    dialog = SettingsDialog(FakeApiClient())
    assert dialog.minutes_input.value() == 10


def test_control_side_can_be_changed_and_saved(qapp):
    client = FakeApiClient()
    dialog = SettingsDialog(client)
    dialog.side_input.setCurrentIndex(dialog.side_input.findData("left"))
    dialog.submit()
    assert client.sent["gesture_control_side"] == "left"
    restored = SettingsDialog(client)
    assert restored.side_input.currentData() == "left"


def test_cp_03_13_guarda_el_nuevo_tiempo(qapp):
    client = FakeApiClient()
    dialog = SettingsDialog(client)
    dialog.minutes_input.setValue(15)

    dialog.submit()

    # Los gestos y la voz se controlan con los interruptores de la ventana principal.
    assert client.sent == {"inactivity_break_minutes": 15, "gesture_control_side": "right"}
    assert dialog.result() == dialog.DialogCode.Accepted


def test_sin_cambios_se_mantienen_los_10_minutos(qapp):
    client = FakeApiClient()
    SettingsDialog(client).submit()
    assert client.sent["inactivity_break_minutes"] == 10


def test_cp_03_14_el_campo_no_admite_valores_no_validos(qapp):
    dialog = SettingsDialog(FakeApiClient())
    dialog.minutes_input.setValue(0)
    assert dialog.minutes_input.value() == 1  # el mínimo es 1 minuto
    dialog.minutes_input.setValue(-5)
    assert dialog.minutes_input.value() == 1
    dialog.minutes_input.setValue(MAX_MINUTES + 100)
    assert dialog.minutes_input.value() == MAX_MINUTES


def test_si_el_servidor_rechaza_el_cambio_muestra_el_error_y_no_se_cierra(qapp):
    error = ApiClientError("Los datos enviados no son válidos.", 422)
    dialog = SettingsDialog(FakeApiClient(error))

    dialog.submit()

    assert dialog.error_label.text() == "Los datos enviados no son válidos."
    assert dialog.result() != dialog.DialogCode.Accepted
