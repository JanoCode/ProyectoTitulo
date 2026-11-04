"""Ventanas de inicio de sesión y registro (PB-33 y PB-48; diseño del Sprint 04)."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout

from ergosense.api_client import ApiClientError
from ergosense.ui import icons, theme
from ergosense.ui.widgets import button, label, restyle

REQUIRED_FIELD = "Completa este campo para continuar"


def make_error_label() -> QLabel:
    """Etiqueta vacía para mostrar en rojo el mensaje en español del servidor."""
    widget = label("", "formError", wrap=True)
    widget.setAlignment(Qt.AlignmentFlag.AlignLeft)
    return widget


class Field:
    """Un campo con su título arriba y su mensaje de error abajo."""

    def __init__(self, layout, title, password=False):
        layout.addWidget(label(title, "fieldLabel"))
        self.input = QLineEdit()
        self.input.setMinimumHeight(38)
        layout.addWidget(self.input)
        self.error = label("", "fieldError")
        self.error.hide()
        layout.addWidget(self.error)
        layout.addSpacing(8)
        if password:
            self.input.setEchoMode(QLineEdit.EchoMode.Password)
            # El ojo muestra u oculta la contraseña, para revisar lo que se escribió.
            self._eye = self.input.addAction(
                icons.icon("eye", theme.MUTED, 18),
                QLineEdit.ActionPosition.TrailingPosition,
            )
            self._eye.setToolTip("Mostrar contraseña")
            self._eye.triggered.connect(self._toggle_visibility)

    def _toggle_visibility(self):
        hidden = self.input.echoMode() == QLineEdit.EchoMode.Password
        self.input.setEchoMode(
            QLineEdit.EchoMode.Normal if hidden else QLineEdit.EchoMode.Password
        )
        self._eye.setIcon(icons.icon("eye-off" if hidden else "eye", theme.MUTED, 18))
        self._eye.setToolTip("Ocultar contraseña" if hidden else "Mostrar contraseña")

    def text(self):
        return self.input.text()

    def check_required(self):
        """Marca el campo si está vacío; devuelve True si tiene contenido."""
        filled = bool(self.input.text().strip())
        self.set_error("" if filled else REQUIRED_FIELD)
        return filled

    def set_error(self, text):
        self.error.setText(text)
        self.error.setVisible(bool(text))
        self.input.setProperty("invalid", bool(text))
        # Qt no vuelve a aplicar el estilo solo cuando cambia una propiedad.
        restyle(self.input)


def _header(layout, title, subtitle):
    logo = QLabel()
    logo.setPixmap(icons.pixmap("logo", size=48))
    logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(logo)
    layout.addSpacing(10)
    title_label = label(title, "loginTitle")
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(title_label)
    subtitle_label = label(subtitle, "muted", wrap=True)
    subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(subtitle_label)
    layout.addSpacing(22)


class RegisterDialog(QDialog):
    """Solicita nombre, correo y contraseña para crear una cuenta."""

    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self._api_client = api_client
        self.registered_email = None
        self.setWindowTitle("ErgoSense")
        self.setWindowIcon(icons.app_icon())
        self.setFixedWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 28)
        layout.setSpacing(4)
        _header(
            layout,
            "Crear cuenta",
            "Usa tu correo y una contraseña de al menos 8 caracteres, con letras y números.",
        )
        self._name = Field(layout, "Nombre")
        self._email = Field(layout, "Correo electrónico")
        self._password = Field(layout, "Contraseña", password=True)
        self.name_input = self._name.input
        self.email_input = self._email.input
        self.password_input = self._password.input

        self.error_label = make_error_label()
        layout.addWidget(self.error_label)
        submit = button("Crear cuenta", "primary")
        submit.setMinimumHeight(40)
        submit.setDefault(True)
        submit.clicked.connect(self.submit)
        layout.addWidget(submit)
        back = button("Ya tengo una cuenta", "link")
        back.clicked.connect(self.reject)
        layout.addSpacing(6)
        layout.addWidget(back, 0, Qt.AlignmentFlag.AlignHCenter)

    def submit(self) -> None:
        """Envía el formulario y mantiene abierta la ventana si existe un error."""
        # Se revisan todos los campos, para marcar de una vez todos los que faltan.
        results = [
            field.check_required()
            for field in (self._name, self._email, self._password)
        ]
        if not all(results):
            return
        try:
            self._api_client.register(
                self.name_input.text(),
                self.email_input.text(),
                self.password_input.text(),
            )
        except ApiClientError as error:
            self.error_label.setText(str(error))
            return
        self.registered_email = self.email_input.text().strip()
        self.accept()


class LoginDialog(QDialog):
    """Inicia sesión y ofrece acceso a la ventana de registro."""

    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self._api_client = api_client
        self.setWindowTitle("ErgoSense")
        self.setWindowIcon(icons.app_icon())
        self.setFixedWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 28)
        layout.setSpacing(4)
        _header(
            layout,
            "ErgoSense",
            "Controla tu computador con gestos y voz, y recuerda hacer pausas.",
        )
        self._email = Field(layout, "Correo electrónico")
        self._password = Field(layout, "Contraseña", password=True)
        self.email_input = self._email.input
        self.password_input = self._password.input

        self.error_label = make_error_label()
        layout.addWidget(self.error_label)
        self.login_button = button("Iniciar sesión", "primary")
        self.login_button.setMinimumHeight(40)
        self.login_button.setDefault(True)  # Enter también inicia sesión
        self.login_button.clicked.connect(self.submit)
        layout.addWidget(self.login_button)
        register = button("Crear cuenta", "link")
        register.clicked.connect(self.open_register)
        layout.addSpacing(6)
        layout.addWidget(register, 0, Qt.AlignmentFlag.AlignHCenter)

    def submit(self) -> None:
        """Revisa que no falten datos y después consulta al servidor."""
        self.error_label.setProperty("role", "formError")
        restyle(self.error_label)
        results = [self._email.check_required(), self._password.check_required()]
        if not all(results):
            return
        try:
            self._api_client.login(
                self.email_input.text(),
                self.password_input.text(),
            )
        except ApiClientError as error:
            self.error_label.setText(str(error))
            return
        self.accept()

    def open_register(self) -> None:
        dialog = RegisterDialog(self._api_client, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.email_input.setText(dialog.registered_email or "")
            self.password_input.clear()
            self.error_label.setProperty("role", "formSuccess")
            restyle(self.error_label)
            self.error_label.setText("Cuenta creada. Ahora puedes iniciar sesión.")
