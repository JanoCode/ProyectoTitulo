"""Ventana principal de ErgoSense (Sprint 04: PB-17 a PB-20).

Muestra la cámara, los controles con la mano y por voz, y la actividad del período.
Solo muestra datos y pide cambios mediante señales: no calcula tiempos ni toca el
hardware. Los métodos show_* los llaman el controlador, las preferencias y los hilos
de gestos y voz.
"""

import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from ergosense.ui import icons, theme
from ergosense.ui.formatting import format_duration, format_elapsed
from ergosense.ui.help_dialog import GESTURES_TAB, VOICE_TAB, HelpDialog
from ergosense.ui.pause_dialog import ALERT_TITLE, NOTIFICATION_MESSAGE, PauseDialog
from ergosense.ui.widgets import (
    CameraPlaceholder,
    CameraView,
    IconBadge,
    InfoBox,
    StatusIndicator,
    Toast,
    ToggleSwitch,
    button,
    divider,
    icon_label,
    label,
)

# Cómo se muestra cada gesto (PB-08). Las claves son los nombres de los gestos de
# ergosense.gestures.classifier.
GESTURE_LABELS = {
    "point": "mover el cursor",
    "thumb_in": "clic izquierdo",
    "index_down": "clic derecho",
    "two_fingers": "desplazamiento",
    "fist": "puño",
    "l_shape": "L",
}

# Estados que informa el hilo de voz: texto, color del punto y si el micrófono está
# en uso (PB-17).
VOICE_STATES = {
    "Desactivado": ("Desactivado", "off", False),
    "Iniciando micrófono...": ("Iniciando el micrófono", "waiting", False),
    "Activo · micrófono en uso": ("Escuchando", "ok", True),
    "Micrófono no disponible": ("Micrófono no disponible", "error", False),
    "Falta el modelo de voz": ("Falta el modelo de voz", "error", False),
    "No se pudo descargar": ("No se pudo descargar", "error", False),
}
# La primera vez se descarga el modelo: "Descargando voz · 45 %".
VOICE_DOWNLOADING = "Descargando voz"
# Texto de ayuda bajo la tarjeta, para los estados que lo necesitan.
VOICE_DETAILS = {
    VOICE_DOWNLOADING: "Solo la primera vez: se descargan unos 40 MB. Después, la voz "
    "funciona sin internet.",
    "No se pudo descargar": "Revisa tu conexión a internet y vuelve a activar la voz.",
}


def _device_name(name):
    """Quita el prefijo que agrega Windows: "Micrófono (2- H510" pasa a "H510"."""
    cleaned = re.sub(
        r"^(micr[oó]fono|microphone)\s*\((\d+-\s*)?", "", name, flags=re.IGNORECASE
    )
    return cleaned.rstrip(") ").strip() or name


def _initials(name):
    words = [word for word in name.split() if word]
    return "".join(word[0] for word in words[:2]).upper() or "?"


class MainWindow(QWidget):
    """Ventana que solo muestra datos; no calcula tiempos."""

    logout_requested = Signal()
    settings_requested = Signal()  # el usuario quiere abrir la configuración
    feature_requested = Signal(str, bool)  # activar o desactivar gestos o voz
    camera_requested = Signal(bool)  # encender o apagar la cámara

    def __init__(self, tray=None):
        super().__init__()  # prepara la parte de QWidget; va siempre primero
        self.setObjectName("window")
        self.setWindowTitle("ErgoSense")
        self.setWindowIcon(icons.app_icon())
        self.resize(1150, 720)
        self.setMinimumSize(960, 620)

        # Ícono de la bandeja para las notificaciones de Windows; puede no existir.
        self._tray = tray
        # Las señales de los hilos llegan con un pequeño retraso. Si los gestos o la
        # voz ya se desactivaron, una señal atrasada no debe volver a mostrarlos activos.
        self._gestures_active = False
        self._voice_enabled = False
        self._hand_present = False
        self._last_gesture = "none"
        self._camera_state = "off"  # off, starting, on o unavailable

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_camera_panel(), 1)
        body.addWidget(self._build_sidebar())
        root.addLayout(body, 1)
        root.addWidget(self._build_status_bar())

        self.toast = Toast(self)
        self.pause_dialog = PauseDialog(self)
        self.show_camera_off()

    # ---------- construcción

    def _build_header(self):
        header = QFrame()
        header.setObjectName("header")
        row = QHBoxLayout(header)
        row.setContentsMargins(16, 10, 16, 10)
        row.addWidget(icon_label("logo", size=30))
        row.addSpacing(6)
        row.addWidget(label("ErgoSense", "brand"))
        row.addStretch()
        self.help_button = button("Ayuda", "ghost", "help")
        self.help_button.clicked.connect(lambda: self.open_help(GESTURES_TAB))
        self.settings_button = button("Configuración", "ghost", "settings")
        self.settings_button.clicked.connect(self.settings_requested.emit)
        row.addWidget(self.help_button)
        row.addWidget(self.settings_button)
        row.addSpacing(8)
        row.addWidget(divider(vertical=True))
        row.addSpacing(8)
        row.addWidget(self._build_user_button())
        return header

    def _build_user_button(self):
        self.user_button = QToolButton()
        self.user_button.setObjectName("userButton")
        self.user_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.user_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        content = QHBoxLayout(self.user_button)
        content.setContentsMargins(6, 2, 6, 2)
        content.setSpacing(8)
        self.avatar = QLabel("?")
        self.avatar.setFixedSize(30, 30)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setStyleSheet(
            f"background: #DCE6F3; color: {theme.PRIMARY}; border-radius: 15px;"
            " font-weight: 600; font-size: 9pt;"
        )
        self.user_name_label = label("")
        content.addWidget(self.avatar)
        content.addWidget(self.user_name_label)
        content.addWidget(icon_label("chevron-down", theme.MUTED, 14))
        self.user_button.setMinimumHeight(40)
        self._fit_user_button()

        menu = QMenu(self)
        account = QWidget()
        account_layout = QVBoxLayout(account)
        account_layout.setContentsMargins(18, 8, 18, 8)
        account_layout.setSpacing(2)
        self.menu_name_label = label("", "fieldLabel")
        self.menu_email_label = label("", "muted")
        account_layout.addWidget(self.menu_name_label)
        account_layout.addWidget(self.menu_email_label)
        account_action = QWidgetAction(menu)
        account_action.setDefaultWidget(account)
        menu.addAction(account_action)
        menu.addSeparator()
        self.logout_action = menu.addAction(
            icons.icon("log-out", theme.TEXT, 16), "Cerrar sesión"
        )
        self.logout_action.triggered.connect(self.logout_requested.emit)
        self.user_button.setMenu(menu)
        return self.user_button

    def _build_camera_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 10)
        layout.setSpacing(10)
        top = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        titles.addWidget(label("Cámara", "h1"))
        titles.addWidget(
            label("Comprueba tu encuadre y el reconocimiento de la mano.", "muted")
        )
        top.addLayout(titles)
        top.addStretch()
        self.camera_button = button("Apagar cámara", "secondary", "video-off")
        self.camera_button.clicked.connect(lambda: self.camera_requested.emit(False))
        top.addWidget(self.camera_button, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(top)

        self.placeholder = CameraPlaceholder()
        self.placeholder.action.clicked.connect(
            lambda: self.camera_requested.emit(True)
        )
        self.camera_view = CameraView()
        self.camera_stack = QStackedWidget()
        self.camera_stack.addWidget(self.placeholder)
        self.camera_stack.addWidget(self.camera_view)
        layout.addWidget(self.camera_stack, 1)

        self.tracking_checkbox = QCheckBox("Mostrar seguimiento de la mano")
        self.tracking_checkbox.setChecked(True)
        self.tracking_checkbox.toggled.connect(self._set_tracking)
        layout.addWidget(self.tracking_checkbox)
        return panel

    def _feature_card(self, icon_name, title, description, link_text, on_link):
        card = QWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        top = QHBoxLayout()
        top.setSpacing(12)
        top.addWidget(IconBadge(icon_name), 0, Qt.AlignmentFlag.AlignTop)
        texts = QVBoxLayout()
        texts.setSpacing(2)
        texts.addWidget(label(title, "h2"))
        texts.addWidget(label(description, "muted", wrap=True))
        top.addLayout(texts, 1)
        toggle = ToggleSwitch()
        top.addWidget(toggle, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(top)
        bottom = QHBoxLayout()
        bottom.setContentsMargins(48, 0, 0, 0)
        status = StatusIndicator("Desactivado", "off", small=True)
        bottom.addWidget(status, 1)
        link = button(link_text, "link")
        link.clicked.connect(on_link)
        bottom.addWidget(link)
        layout.addLayout(bottom)
        return card, toggle, status

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(320)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        card, self.gesture_toggle, self.gesture_status = self._feature_card(
            "hand",
            "Control con la mano",
            "Mueve el cursor y realiza acciones con gestos",
            "Ver gestos",
            lambda: self.open_help(GESTURES_TAB),
        )
        self.gesture_toggle.clicked.connect(
            lambda checked: self.feature_requested.emit("gesture_enabled", checked)
        )
        layout.addWidget(card)
        layout.addWidget(divider())

        card, self.voice_toggle, self.voice_status = self._feature_card(
            "mic",
            "Control por voz",
            "Realiza acciones diciendo un comando",
            "Ver comandos",
            lambda: self.open_help(VOICE_TAB),
        )
        self.voice_toggle.clicked.connect(
            lambda checked: self.feature_requested.emit("voice_enabled", checked)
        )
        layout.addWidget(card)
        # Qué micrófono se está usando, que ayuda si Windows tiene elegido otro, o
        # el avance de la descarga del modelo la primera vez.
        self.microphone_label = label("", "small", wrap=True)
        self.microphone_label.hide()
        # El usuario debe saber qué pasa con su audio (RNF-17).
        voice_notice = InfoBox(
            "El audio se procesa en este equipo, sin internet, y no se guarda.",
            kind="note",
        )
        notice = QVBoxLayout()
        notice.setContentsMargins(48, 0, 0, 0)
        notice.setSpacing(8)
        notice.addWidget(self.microphone_label)
        notice.addWidget(voice_notice)
        layout.addLayout(notice)
        layout.addWidget(divider())

        activity = QHBoxLayout()
        activity.setSpacing(12)
        activity.addWidget(IconBadge("clock"), 0, Qt.AlignmentFlag.AlignTop)
        texts = QVBoxLayout()
        texts.setSpacing(2)
        texts.addWidget(label("Actividad y pausas", "h2"))
        texts.addWidget(label("Período actual", "muted"))
        texts.addSpacing(10)
        self.period_label = label("--:--:--", "timer")
        texts.addWidget(self.period_label)
        texts.addWidget(
            label(
                "Te recordaremos hacer una pausa cada 60 minutos.", "muted", wrap=True
            )
        )
        texts.addSpacing(8)
        last = QHBoxLayout()
        last.addWidget(label("Última actividad", "small"))
        last.addStretch()
        self.activity_label = label("Sin actividad aún", "fieldLabel")
        last.addWidget(self.activity_label)
        texts.addLayout(last)
        texts.addSpacing(6)
        preview = button("Ver recordatorio de pausa", "link")
        preview.clicked.connect(self.pause_dialog_preview)
        texts.addWidget(preview, 0, Qt.AlignmentFlag.AlignLeft)
        activity.addLayout(texts, 1)
        layout.addLayout(activity)
        layout.addStretch()
        return sidebar

    def _build_status_bar(self):
        bar = QFrame()
        bar.setObjectName("statusBar")
        row = QHBoxLayout(bar)
        row.setContentsMargins(14, 6, 14, 6)
        row.setSpacing(6)
        self._connection_icon = icon_label("wifi", theme.MUTED, 14)
        self.connection_label = label("Conectado", "small")
        row.addWidget(self._connection_icon)
        row.addWidget(self.connection_label)
        row.addStretch()
        # Indicadores visibles mientras la cámara o el micrófono están en uso (PB-17).
        self.camera_indicator = StatusIndicator(
            "Cámara en uso", "info", small=True, stretch=False
        )
        self.mic_indicator = StatusIndicator(
            "Micrófono en uso", "waiting", small=True, stretch=False
        )
        for indicator in (self.camera_indicator, self.mic_indicator):
            indicator.hide()
            row.addWidget(indicator)
            row.addSpacing(10)
        return bar

    # ---------- acciones de la ventana

    def open_help(self, tab=GESTURES_TAB):
        HelpDialog(self, tab).exec()

    def pause_dialog_preview(self):
        """Muestra cómo se ve el aviso de pausa, sin esperar los 60 minutos."""
        self.pause_dialog.show()
        self.pause_dialog.raise_()

    def _set_tracking(self, visible):
        self.camera_view.show_tracking = visible
        self.camera_view.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.toast.reposition()

    # ---------- monitoreo (PB-01, PB-05)

    def show_period(self, seconds):
        """Muestra el tiempo del período en la ventana."""
        self.period_label.setText(format_duration(seconds))

    def show_last_activity(self, seconds):
        """Muestra hace cuánto fue la última actividad, por ejemplo "hace 12 segundos"."""
        self.activity_label.setText(format_elapsed(seconds))

    def show_alert(self):
        """Muestra el aviso de pausa, y también como notificación si la ventana no está al frente."""
        self.pause_dialog.show()
        self.pause_dialog.raise_()
        # Minimizada o en segundo plano: el usuario no ve la ventana, así que se avisa por la bandeja.
        if self._tray is not None and (self.isMinimized() or not self.isActiveWindow()):
            self._tray.showMessage(ALERT_TITLE, NOTIFICATION_MESSAGE)

    # ---------- cuenta y conexión

    def show_user(self, name: str, email: str) -> None:
        """Muestra qué cuenta posee la sesión de uso actual."""
        self.user_name_label.setText(name)
        self.avatar.setText(_initials(name))
        self.menu_name_label.setText(name)
        self.menu_email_label.setText(email)
        self._fit_user_button()

    def _fit_user_button(self):
        # El botón no calcula solo el ancho de lo que lleva dentro: se le indica.
        self.user_button.setMinimumWidth(
            self.user_button.layout().sizeHint().width() + 4
        )

    def show_connection(self, connected):
        """Indica en la barra de estado si hay conexión con el servidor."""
        self.connection_label.setText(
            "Conectado" if connected else "Sin conexión con el servidor"
        )
        color = theme.MUTED if connected else theme.DANGER
        self._connection_icon.setPixmap(
            icons.pixmap("wifi" if connected else "wifi-off", color, 14)
        )

    def show_toast(self, text, kind="success"):
        """Muestra un mensaje breve abajo de la ventana."""
        self.toast.show_message(text, kind)

    # ---------- cámara

    def show_camera_starting(self):
        self._camera_state = "starting"
        self.placeholder.set_content(
            "video", "Iniciando la cámara...", "Espera un momento."
        )
        self.camera_stack.setCurrentWidget(self.placeholder)
        self.camera_button.show()
        self.camera_indicator.show()
        if self._gestures_active:
            # Al reintentar, la tarjeta deja de decir "Cámara no disponible".
            self._show_hand_status()

    def show_frame(self, image, points):
        """Recibe un cuadro del hilo de gestos para la vista previa."""
        if self._camera_state not in ("starting", "on"):
            return  # cuadro atrasado de una cámara que ya se apagó
        if self._camera_state == "starting":
            self._camera_state = "on"
            self.camera_stack.setCurrentWidget(self.camera_view)
        self.camera_view.set_frame(image, points)

    def show_camera_off(self):
        self._camera_state = "off"
        self.camera_view.clear()
        self.placeholder.set_content(
            "video-off",
            "La cámara está apagada",
            "Puedes encenderla solo para ver el video. Esto no activa los gestos.",
            "Encender cámara",
            "video",
        )
        self.camera_stack.setCurrentWidget(self.placeholder)
        self.camera_button.hide()
        self.camera_indicator.hide()

    def show_camera_unavailable(self):
        """Informa que no hay cámara; el resto de ErgoSense sigue funcionando (PB-07)."""
        self._camera_state = "unavailable"
        self.camera_view.clear()
        self.placeholder.set_content(
            "video-off",
            "No hay una cámara disponible",
            "Conecta una cámara y vuelve a intentarlo. Las demás funciones de "
            "ErgoSense siguen disponibles.",
            "Reintentar",
            "video",
        )
        self.camera_stack.setCurrentWidget(self.placeholder)
        self.camera_button.hide()
        self.camera_indicator.hide()
        # Los gestos siguen activados en la cuenta: al volver la cámara, con
        # «Reintentar», la tarjeta vuelve a mostrar si ve la mano.
        self._hand_present = False
        if self._gestures_active:
            self.gesture_status.set_status("Cámara no disponible", "error")

    # ---------- control con la mano

    def show_gestures_starting(self):
        """Muestra que el control con la mano está activado y busca la mano."""
        self._gestures_active = True
        self.gesture_toggle.set_checked_silently(True)
        self._show_hand_status()
        self._show_gesture_badge()
        if self._camera_state in ("off", "unavailable"):
            self.show_camera_starting()

    def show_hand(self, present):
        """El hilo de gestos avisa que la mano apareció o salió de la imagen."""
        self._hand_present = present
        if self._gestures_active:
            self._show_hand_status()

    def _show_hand_status(self):
        if self._hand_present:
            self.gesture_status.set_status("Mano detectada", "ok")
        else:
            self.gesture_status.set_status("Buscando tu mano", "waiting")

    def show_gesture(self, gesture):
        """Muestra sobre la imagen qué gesto se reconoce ahora."""
        # Se recuerda siempre: si los gestos se activan con la cámara encendida, el
        # gesto que ya se estaba haciendo debe aparecer de inmediato.
        self._last_gesture = gesture
        if self._gestures_active:
            self._show_gesture_badge()

    def _show_gesture_badge(self):
        name = GESTURE_LABELS.get(self._last_gesture)
        self.camera_view.gesture_text = f"Gesto detectado: {name}" if name else ""
        self.camera_view.update()

    def show_gestures_disabled(self):
        """Muestra que el control con la mano está desactivado."""
        self._gestures_active = False
        self.gesture_toggle.set_checked_silently(False)
        self.gesture_status.set_status("Desactivado", "off")
        self.camera_view.gesture_text = ""
        self.camera_view.update()

    # ---------- control por voz

    def set_voice_enabled(self, enabled):
        self._voice_enabled = enabled
        self.voice_toggle.set_checked_silently(enabled)
        if not enabled:
            self.voice_status.set_status("Desactivado", "off")
            self.mic_indicator.hide()
            self.microphone_label.hide()

    def show_voice_status(self, status):
        if not self._voice_enabled:
            return  # señal atrasada de un micrófono que ya se cerró
        text, state, microphone_in_use = VOICE_STATES.get(
            status, (status, "waiting", False)
        )
        self.voice_status.set_status(text, state)
        self.mic_indicator.setVisible(microphone_in_use)
        downloading = status.startswith(VOICE_DOWNLOADING)
        detail = VOICE_DETAILS.get(VOICE_DOWNLOADING if downloading else status)
        if detail:
            self.microphone_label.setText(detail)
            self.microphone_label.show()
        elif not microphone_in_use:
            # El nombre del micrófono solo se muestra mientras se escucha.
            self.microphone_label.hide()

    def show_microphone(self, name):
        """Muestra el micrófono que usa la voz, el predeterminado de Windows."""
        if not self._voice_enabled or not name:
            return
        self.microphone_label.setText(f"Micrófono: {_device_name(name)}")
        self.microphone_label.show()
