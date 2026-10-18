"""Ventana principal del monitoreo y cierre de sesión."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFormLayout, QLabel, QPushButton, QWidget

from ergosense.ui.formatting import format_duration

# Contenido del aviso de uso prolongado (PB-05).
ALERT_TITLE = "ErgoSense: hora de una pausa"
ALERT_MESSAGE = "Llevas 60 minutos de actividad. Te recomendamos realizar una pausa."

# Cómo se muestra cada gesto en la ventana (PB-08). Las claves son los nombres de
# los gestos de ergosense.gestures.classifier.
GESTURE_LABELS = {
    "none": "sin gesto",
    "point": "mover el cursor",
    "thumb_in": "click izquierdo",
    "index_down": "click derecho",
    "two_fingers": "scroll",
    "fist": "puño",
    "l_shape": "L",
}
GESTURES_DISABLED = "Desactivado"
GESTURES_STARTING = "Iniciando la cámara..."
CAMERA_UNAVAILABLE = "No hay una cámara disponible"


class MainWindow(QWidget):
    """Ventana que solo muestra datos; no calcula tiempos."""

    logout_requested = Signal()
    settings_requested = Signal()  # el usuario quiere abrir la configuración

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
        self.user_label = QLabel("Sesión iniciada")
        # Estado del control por gestos: desactivado, sin cámara o el gesto actual.
        self.gesture_label = QLabel(GESTURES_DISABLED)
        # Las señales del hilo de gestos llegan con un pequeño retraso. Si los gestos
        # ya se desactivaron, una señal atrasada no debe volver a mostrarlos activos.
        self._gestures_active = False
        self.settings_button = QPushButton("Configuración")
        self.settings_button.clicked.connect(self.settings_requested.emit)
        self.logout_button = QPushButton("Cerrar sesión")
        self.logout_button.clicked.connect(self.logout_requested.emit)

        # QFormLayout ordena filas del tipo "nombre: valor", una debajo de otra.
        layout = QFormLayout()
        layout.addRow("Cuenta:", self.user_label)
        layout.addRow("Período:", self.period_label)
        layout.addRow("Última actividad:", self.activity_label)
        layout.addRow("Gestos:", self.gesture_label)
        layout.addRow(self.alert_label)  # un solo widget ocupa la fila completa
        layout.addRow(self.settings_button)
        layout.addRow(self.logout_button)
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

    def show_user(self, name: str, email: str) -> None:
        """Muestra qué cuenta posee la sesión de uso actual."""
        self.user_label.setText(f"{name} ({email})")

    def show_gestures_starting(self):
        """Muestra que se está abriendo la cámara para el control por gestos."""
        self._gestures_active = True
        self.gesture_label.setText(GESTURES_STARTING)

    def show_gesture(self, gesture):
        """Muestra que los gestos están activos y cuál se reconoce ahora."""
        if not self._gestures_active:
            return  # señal atrasada de un hilo que ya se detuvo
        self.gesture_label.setText(f"Activo: {GESTURE_LABELS.get(gesture, gesture)}")

    def show_gestures_disabled(self):
        """Muestra que el control por gestos está desactivado."""
        self._gestures_active = False
        self.gesture_label.setText(GESTURES_DISABLED)

    def show_camera_unavailable(self):
        """Informa que no hay cámara; el resto de ErgoSense sigue funcionando (PB-07)."""
        self._gestures_active = False
        self.gesture_label.setText(CAMERA_UNAVAILABLE)
