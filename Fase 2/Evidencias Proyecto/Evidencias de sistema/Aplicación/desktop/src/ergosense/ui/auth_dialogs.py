"""Ventanas básicas de registro e inicio de sesión del Sprint 02."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from ergosense.api_client import ApiClientError


def make_error_label() -> QLabel:
    """Crea una etiqueta visible pero vacía para mensajes en español."""
    label = QLabel("")
    label.setWordWrap(True)
    label.setStyleSheet("color: #b00020;")
    label.setAlignment(Qt.AlignmentFlag.AlignLeft)
    return label


class RegisterDialog(QDialog):
    """Solicita nombre, correo y contraseña para crear una cuenta."""

    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self._api_client = api_client
        self.registered_email = None
        self.setWindowTitle("Crear cuenta de ErgoSense")

        self.name_input = QLineEdit()
        self.email_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.error_label = make_error_label()

        form = QFormLayout()
        form.addRow("Nombre:", self.name_input)
        form.addRow("Correo electrónico:", self.email_input)
        form.addRow("Contraseña:", self.password_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Crear cuenta")
        buttons.accepted.connect(self.submit)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(
            QLabel("La contraseña debe tener al menos 8 caracteres, letras y números.")
        )
        layout.addWidget(self.error_label)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def submit(self) -> None:
        """Envía el formulario y mantiene abierta la ventana si existe un error."""
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
        self.setWindowTitle("Iniciar sesión en ErgoSense")

        self.email_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.error_label = make_error_label()

        form = QFormLayout()
        form.addRow("Correo electrónico:", self.email_input)
        form.addRow("Contraseña:", self.password_input)

        login_button = QPushButton("Iniciar sesión")
        register_button = QPushButton("Crear una cuenta")
        cancel_button = QPushButton("Salir")
        login_button.clicked.connect(self.submit)
        register_button.clicked.connect(self.open_register)
        cancel_button.clicked.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.error_label)
        layout.addWidget(login_button)
        layout.addWidget(register_button)
        layout.addWidget(cancel_button)
        self.setLayout(layout)

    def submit(self) -> None:
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
            self.error_label.setStyleSheet("color: #176b2c;")
            self.error_label.setText("Cuenta creada. Ahora puedes iniciar sesión.")
