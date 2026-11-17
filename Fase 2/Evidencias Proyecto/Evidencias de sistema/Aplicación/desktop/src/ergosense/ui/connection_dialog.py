from PySide6.QtWidgets import QDialog, QLineEdit, QVBoxLayout

from ergosense.api_client import ApiClientError
from ergosense.app.connection import normalize_api_url, save_server_url
from ergosense.ui.widgets import button, label


class ConnectionDialog(QDialog):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self._api_client = api_client
        self.setWindowTitle("Conexión de ErgoSense")
        self.setMinimumWidth(460)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(label("Servidor", "sectionTitle"))
        layout.addWidget(label(
            "En otro computador, usa la dirección del equipo donde está funcionando "
            "el servidor. Para conectarte desde internet, usa su dirección HTTPS.",
            "muted", wrap=True,
        ))
        self.url_input = QLineEdit(api_client.base_url)
        self.url_input.setPlaceholderText("http://192.168.1.20:8000/api/v1")
        self.url_input.setMinimumHeight(38)
        layout.addWidget(self.url_input)
        self.error_label = label("", "formError", wrap=True)
        layout.addWidget(self.error_label)
        self.save_button = button("Comprobar y guardar", "primary")
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self.submit)
        layout.addWidget(self.save_button)
        cancel = button("Cancelar", "secondary")
        cancel.clicked.connect(self.reject)
        layout.addWidget(cancel)

    def submit(self):
        self.save_button.setEnabled(False)
        try:
            url = normalize_api_url(self.url_input.text())
            self._api_client.check_server(url)
            save_server_url(url)
            self._api_client.change_server(url)
        except (ValueError, OSError, ApiClientError) as error:
            self.error_label.setText(str(error))
        else:
            self.accept()
        finally:
            self.save_button.setEnabled(True)
