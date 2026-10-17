"""Sección básica de configuración del Sprint 03 (PB-36 y PB-37).

Permite cambiar el tiempo de inactividad y activar o desactivar los gestos y la
voz. La interfaz completa se desarrolla en el Sprint 04.
"""

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)

from ergosense.api_client import ApiClientError
from ergosense.ui.auth_dialogs import make_error_label

# El campo solo admite enteros en este rango, así que un valor no válido como 0,
# un negativo o un decimal no se puede escribir (CP-03-14). El servidor también
# lo valida. El máximo, una jornada de 8 horas, evita errores de tipeo.
MIN_MINUTES = 1
MAX_MINUTES = 480


class SettingsDialog(QDialog):
    """Muestra la configuración actual y guarda los cambios en el servidor."""

    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self._api_client = api_client
        self.setWindowTitle("Configuración de ErgoSense")
        settings = api_client.settings

        self.minutes_input = QSpinBox()
        self.minutes_input.setRange(MIN_MINUTES, MAX_MINUTES)
        self.minutes_input.setSuffix(" min")
        self.minutes_input.setValue(settings["inactivity_break_minutes"])
        self.gestures_input = QCheckBox("Control mediante gestos")
        self.gestures_input.setChecked(settings["gesture_enabled"])
        # La voz llega en el Sprint 04; su preferencia ya se guarda (PB-36).
        self.voice_input = QCheckBox("Control por voz (aún no disponible)")
        self.voice_input.setChecked(settings["voice_enabled"])
        self.error_label = make_error_label()

        form = QFormLayout()
        form.addRow(
            "Tiempo de inactividad para registrar una pausa:", self.minutes_input
        )
        form.addRow(self.gestures_input)
        form.addRow(self.voice_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Guardar")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.accepted.connect(self.submit)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        # El aviso de 60 minutos no es configurable (PB-37); se aclara para evitar dudas.
        layout.addWidget(QLabel("El aviso de pausa a los 60 minutos no se modifica."))
        layout.addWidget(self.error_label)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def submit(self) -> None:
        """Envía la configuración y mantiene abierta la ventana si hay un error."""
        try:
            self._api_client.update_settings(
                {
                    "inactivity_break_minutes": self.minutes_input.value(),
                    "gesture_enabled": self.gestures_input.isChecked(),
                    "voice_enabled": self.voice_input.isChecked(),
                }
            )
        except ApiClientError as error:
            # Si el servidor rechaza el cambio, se conserva la configuración anterior.
            self.error_label.setText(str(error))
            return
        self.accept()
