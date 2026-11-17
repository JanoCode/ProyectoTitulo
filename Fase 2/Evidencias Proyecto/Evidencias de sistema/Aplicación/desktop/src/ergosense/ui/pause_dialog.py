"""Aviso de pausa a los 60 minutos de actividad (PB-05 y PB-19)."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout

from ergosense.ui import icons, theme
from ergosense.ui.widgets import button, label

ALERT_TITLE = "Es momento de hacer una pausa"
ALERT_MESSAGE = (
    "Llevas 60 minutos de actividad. Te recomendamos descansar unos minutos."
)
# Texto de la notificación de Windows, cuando la ventana no está a la vista.
NOTIFICATION_MESSAGE = "Llevas 60 minutos de actividad. Descansa unos minutos."


class PauseDialog(QDialog):
    """Ventana del aviso. No es modal: no bloquea el resto de la aplicación."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ErgoSense")
        self.setModal(False)
        self.setFixedWidth(440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 28)
        layout.setSpacing(8)
        badge = QLabel()
        badge.setFixedSize(56, 56)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setPixmap(icons.pixmap("clock", theme.PRIMARY, 28))
        badge.setStyleSheet(f"background: {theme.INFO_BG}; border-radius: 28px;")
        layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(8)
        self.title_label = label(ALERT_TITLE, "dialogTitle")
        self.message_label = label(ALERT_MESSAGE, "muted", wrap=True)
        note = label(
            "Este aviso no bloquea el computador ni te obliga a descansar.",
            "small",
            wrap=True,
        )
        for widget in (self.title_label, self.message_label, note):
            widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(widget)
        layout.addSpacing(10)
        ok = button("Entendido", "primary")
        ok.setDefault(True)
        ok.clicked.connect(self.accept)
        layout.addWidget(ok, 0, Qt.AlignmentFlag.AlignHCenter)
