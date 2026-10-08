"""Ventana principal: muestra el tiempo del período, la última actividad y el aviso de pausa (PB-01 y PB-05)."""

from PySide6.QtWidgets import QFormLayout, QLabel, QWidget

from ergosense.ui.formatting import format_duration

# Contenido del aviso de uso prolongado (PB-05).
ALERT_TITLE = "ErgoSense: hora de una pausa"
ALERT_MESSAGE = "Llevas 60 minutos de actividad. Te recomendamos realizar una pausa."


class MainWindow(QWidget):
    """Ventana que solo muestra datos; no calcula tiempos."""

    def __init__(self, tray=None):
        super().__init__()  # prepara la parte de QWidget; va siempre primero
        self.setWindowTitle("ErgoSense")

        # Ícono de la bandeja para las notificaciones de Windows; puede no existir.
        self._tray = tray

        # Etiquetas con los valores; parten sin dato hasta la primera actualización.
        self.period_label = QLabel("--:--:--")
        self.activity_label = QLabel("--:--:--")
        # El aviso parte vacío y solo se llena al cumplirse el período.
        self.alert_label = QLabel("")

        # QFormLayout ordena filas del tipo "nombre: valor", una debajo de otra.
        layout = QFormLayout()
        layout.addRow("Período:", self.period_label)
        layout.addRow("Última actividad:", self.activity_label)
        layout.addRow(self.alert_label)  # un solo widget ocupa la fila completa
        self.setLayout(layout)  # asigna el layout a esta ventana

    def show_period(self, seconds):
        """Muestra el tiempo del período en la ventana."""
        self.period_label.setText(format_duration(seconds))

    def show_last_activity(self, seconds):
        """Muestra el tiempo desde la última actividad en la ventana."""
        self.activity_label.setText(format_duration(seconds))

    def show_alert(self):
        """Muestra el aviso de pausa, y también como notificación si la ventana no está al frente."""
        self.alert_label.setText(ALERT_MESSAGE)
        # Minimizada o en segundo plano: el usuario no ve la ventana, así que se avisa por la bandeja.
        if self._tray is not None and (self.isMinimized() or not self.isActiveWindow()):
            self._tray.showMessage(ALERT_TITLE, ALERT_MESSAGE)
