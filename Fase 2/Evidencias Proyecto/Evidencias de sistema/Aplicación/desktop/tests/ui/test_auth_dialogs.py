"""Pruebas de las ventanas básicas de cuenta del Sprint 02."""

from ergosense.api_client import ApiClientError
from ergosense.ui.auth_dialogs import LoginDialog, RegisterDialog


class FakeApiClient:
    def __init__(self, error=None):
        self.error = error
        self.registered = None
        self.logged_in = None

    def register(self, name, email, password):
        if self.error:
            raise self.error
        self.registered = (name, email, password)

    def login(self, email, password):
        if self.error:
            raise self.error
        self.logged_in = (email, password)


def test_ventana_de_registro_envia_los_tres_datos(qapp):
    client = FakeApiClient()
    dialog = RegisterDialog(client)
    dialog.name_input.setText("Alejandro")
    dialog.email_input.setText("a@example.com")
    dialog.password_input.setText("clave123")

    dialog.submit()

    assert client.registered == ("Alejandro", "a@example.com", "clave123")
    assert dialog.result() == dialog.DialogCode.Accepted


def test_ventana_de_login_muestra_el_error_del_servidor(qapp):
    client = FakeApiClient(ApiClientError("Las credenciales son incorrectas.", 401))
    dialog = LoginDialog(client)
    dialog.email_input.setText("a@example.com")
    dialog.password_input.setText("incorrecta")

    dialog.submit()

    assert dialog.result() != dialog.DialogCode.Accepted
    assert dialog.error_label.text() == "Las credenciales son incorrectas."


def test_sin_datos_marca_los_campos_y_no_consulta_al_servidor(qapp):
    client = FakeApiClient()
    dialog = LoginDialog(client)

    dialog.submit()

    assert client.logged_in is None
    assert dialog._email.error.text() == "Completa este campo para continuar"
    assert dialog._password.error.text() == "Completa este campo para continuar"


def test_el_ojo_muestra_y_oculta_la_contrasena(qapp):
    dialog = LoginDialog(FakeApiClient())
    field = dialog._password
    assert field.input.echoMode() == field.input.EchoMode.Password
    field._eye.trigger()
    assert field.input.echoMode() == field.input.EchoMode.Normal
