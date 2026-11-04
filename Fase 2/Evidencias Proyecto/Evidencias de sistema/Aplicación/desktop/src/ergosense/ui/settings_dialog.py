"""Configuración del registro de pausas (PB-36 y PB-37; diseño del Sprint 04).

Los controles de gestos y voz están en la ventana principal; aquí se cambia el
tiempo de inactividad a partir del cual se registra una pausa.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QSpinBox, QVBoxLayout

from ergosense.api_client import ApiClientError
from ergosense.ui import icons
from ergosense.ui.auth_dialogs import make_error_label
from ergosense.ui.widgets import InfoBox, button, divider, label

# El campo solo admite enteros en este rango, así que un valor no válido como 0,
# un negativo o un decimal no se puede escribir (CP-03-14). El servidor también
# lo valida. El máximo, una jornada de 8 horas, evita errores de tipeo.
MIN_MINUTES = 1
MAX_MINUTES = 480


class SettingsDialog(QDialog):
    """Muestra el tiempo de inactividad actual y guarda el cambio en el servidor."""

    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self._api_client = api_client
        self.setWindowTitle("Configuración")
        self.setWindowIcon(icons.app_icon())
        self.setFixedWidth(430)
        settings = api_client.settings

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        body = QVBoxLayout()
        body.setContentsMargins(22, 20, 22, 18)
        body.setSpacing(8)
        body.addWidget(label("Configuración", "dialogTitle"))
        body.addSpacing(8)
        body.addWidget(label("Registro de pausas", "muted"))
        body.addWidget(label("Tiempo de inactividad", "fieldLabel"))
        self.minutes_input = QSpinBox()
        self.minutes_input.setRange(MIN_MINUTES, MAX_MINUTES)
        self.minutes_input.setSuffix("  minutos")
        self.minutes_input.setFixedWidth(180)
        self.minutes_input.setMinimumHeight(38)
        self.minutes_input.setValue(settings["inactivity_break_minutes"])
        body.addWidget(self.minutes_input)
        body.addWidget(
            label(
                "Si no utilizas el teclado o el mouse durante este tiempo, se "
                "registrará una pausa.",
                "muted",
                wrap=True,
            )
        )
        body.addSpacing(4)
        # El aviso de 60 minutos no es configurable (PB-37); se aclara para evitar dudas.
        body.addWidget(InfoBox("El recordatorio cada 60 minutos se mantiene fijo."))
        self.error_label = make_error_label()
        body.addWidget(self.error_label)
        layout.addLayout(body)

        layout.addWidget(divider())
        footer = QHBoxLayout()
        footer.setContentsMargins(22, 14, 22, 14)
        footer.addStretch()
        cancel = button("Cancelar", "secondary")
        cancel.clicked.connect(self.reject)
        save = button("Guardar cambios", "primary")
        save.setDefault(True)
        save.clicked.connect(self.submit)
        footer.addWidget(cancel)
        footer.addWidget(save)
        layout.addLayout(footer)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def submit(self) -> None:
        """Envía el nuevo tiempo y mantiene abierta la ventana si hay un error."""
        try:
            self._api_client.update_settings(
                {"inactivity_break_minutes": self.minutes_input.value()}
            )
        except ApiClientError as error:
            # Si el servidor rechaza el cambio, se conserva la configuración anterior.
            self.error_label.setText(str(error))
            return
        self.accept()
