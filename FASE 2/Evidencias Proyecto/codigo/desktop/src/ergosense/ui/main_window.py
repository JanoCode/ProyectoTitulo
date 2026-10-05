"""Ventana principal: muestra el tiempo del período y de la última actividad (PB-01)."""

from PySide6.QtWidgets import QFormLayout, QLabel, QWidget

from ergosense.ui.formatting import format_duration


class MainWindow(QWidget):
    """Ventana que solo muestra datos; no calcula tiempos."""

    def __init__(self):
        super().__init__()  # prepara la parte de QWidget; va siempre primero
        self.setWindowTitle("ErgoSense")

        # Etiquetas con los valores; parten sin dato hasta la primera actualización.
        self.period_label = QLabel("--:--:--")
        self.activity_label = QLabel("--:--:--")

        # QFormLayout ordena filas del tipo "nombre: valor", una debajo de otra.
        layout = QFormLayout()
        layout.addRow("Período:", self.period_label)
        layout.addRow("Última actividad:", self.activity_label)
        self.setLayout(layout)  # asigna el layout a esta ventana

    def show_period(self, seconds):
        """Muestra el tiempo del período en la ventana."""
        self.period_label.setText(format_duration(seconds))

    def show_last_activity(self, seconds):
        """Muestra el tiempo desde la última actividad en la ventana."""
        self.activity_label.setText(format_duration(seconds))
