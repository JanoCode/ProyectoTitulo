from PySide6.QtCore import QObject, QRectF, Qt, QTimer, Slot
from PySide6.QtGui import QColor, QCursor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QApplication, QWidget

from ergosense.ui import icons

GREEN = "#53DAA1"
AMBER = "#E6B54A"
BLUE = "#78B8FF"
RED = "#FF8A8A"


class FloatingPanel(QWidget):
    def __init__(self, title):
        super().__init__(None,
            Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.WindowDoesNotAcceptFocus,
        )
        self.setWindowTitle(title)
        for attribute in (
            Qt.WidgetAttribute.WA_TranslucentBackground,
            Qt.WidgetAttribute.WA_ShowWithoutActivating,
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
        ):
            self.setAttribute(attribute)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setWindowOpacity(0.94)
        self.setFont(QFont("Segoe UI", 10))

    def reposition(self, offset=20):
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            self.move(area.right() - self.width() - 20, area.top() + offset)

    def painter(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor("#465168"))
        painter.setBrush(QColor("#18202D"))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 12, 12)
        return painter


class ModeIndicator(FloatingPanel):
    def __init__(self):
        super().__init__("Modos de ErgoSense")
        self.items = []

    def set_items(self, items):
        if items == self.items:
            return
        self.items = items
        if not items:
            self.hide()
            return
        metrics = QFontMetrics(self.font())
        width = sum(metrics.horizontalAdvance(text) + 52 for _, text, _ in items)
        self.setFixedSize(width + 8, 44)
        self.reposition()
        self.show()
        self.update()

    def paintEvent(self, event):
        painter = self.painter()
        metrics = QFontMetrics(self.font())
        left = 14
        for icon, text, color in self.items:
            painter.drawPixmap(left, 11, icons.pixmap(icon, color, 22))
            painter.setPen(QColor("#F2F5FA"))
            width = metrics.horizontalAdvance(text)
            painter.drawText(QRectF(left + 30, 0, width, 44), Qt.AlignmentFlag.AlignVCenter, text)
            left += width + 52


class DesktopNotice(FloatingPanel):
    def __init__(self, indicator):
        super().__init__("Aviso de ErgoSense")
        self._indicator = indicator
        self.text = ""
        self.kind = "success"
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)

    def show_message(self, text, kind="success"):
        self.text = text
        self.kind = kind
        metrics = QFontMetrics(self.font())
        bounds = metrics.boundingRect(0, 0, 328, 200, Qt.TextFlag.TextWordWrap, text)
        self.setFixedSize(392, max(60, min(224, bounds.height() + 28)))
        self.reposition(76 if self._indicator.isVisible() else 20)
        self.show()
        self.update()
        self.timer.start(6000 if kind == "error" else 3500)

    def paintEvent(self, event):
        painter = self.painter()
        color = RED if self.kind == "error" else AMBER if self.kind == "waiting" else GREEN
        painter.drawPixmap(14, 18, icons.pixmap("mic" if self.kind == "dictation" else "info", color, 22))
        painter.setPen(QColor("#F2F5FA"))
        painter.drawText(
            self.rect().adjusted(48, 12, -16, -12),
            Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignVCenter, self.text,
        )


class DesktopFeedback(QObject):
    def __init__(self):
        super().__init__()
        self.indicator = ModeIndicator()
        self.notice = DesktopNotice(self.indicator)
        self.gestures = False
        self.voice = False
        self.camera_ready = False
        self.camera_error = False
        self.hand = False
        self.voice_state = "Preparando"
        self.dictating = False
        self.dictation_state = "preparing"
        self._dictation_ready = False
        self._closed = False

    @Slot(str, str)
    def notify(self, text, kind="success"):
        if not self._closed:
            self.notice.show_message(text, kind)

    def set_features(self, settings):
        gestures, voice = settings["gesture_enabled"], settings["voice_enabled"]
        if gestures != self.gestures:
            self.camera_ready = False
            self.camera_error = False
            self.hand = False
        self.gestures, self.voice = gestures, voice
        if not voice:
            self.dictating = False
            self.voice_state = "Desactivada"
        elif self.voice_state == "Desactivada":
            self.voice_state = "Preparando"
        self.refresh()

    @Slot()
    def camera_available(self):
        if self.gestures and not self.camera_ready:
            self.camera_ready = True
            self.camera_error = False
            self.refresh()
            self.notify("Control por gestos listo.")

    @Slot()
    def camera_unavailable(self):
        if self.gestures:
            self.camera_ready = False
            self.camera_error = True
            self.hand = False
            self.refresh()
            self.notify("No se puede usar la cámara. El control por gestos no está disponible.", "error")

    @Slot(bool)
    def hand_changed(self, detected):
        self.hand = detected
        self.refresh()

    @Slot(str)
    def voice_status(self, status):
        if not self.voice:
            return
        previous = self.voice_state
        if status == "Activo · micrófono en uso":
            self.voice_state = "Lista"
            if previous != "Lista":
                self.notify("Control por voz listo. Puedes decir «activar dictado».")
        elif status == "Desactivado":
            self.voice_state = "Desactivada"
        elif status in {"Micrófono no disponible", "Falta el modelo de voz", "No se pudo descargar"}:
            self.voice_state = "No disponible"
            self.notify(status + ". El control por voz no está disponible.", "error")
        else:
            self.voice_state = "Preparando"
        self.refresh()

    @Slot(bool)
    def set_dictation(self, active):
        active = bool(active and self.voice)
        if active == self.dictating:
            return
        self.dictating = active
        self._dictation_ready = False
        self.dictation_state = "preparing"
        self.refresh()
        self.notify("Preparando dictado…" if active else "Dictado desactivado.",
                    "waiting" if active else "success")

    @Slot(str)
    def set_dictation_state(self, state):
        if not self.dictating or state not in {"preparing", "listening", "processing"}:
            return
        self.dictation_state = state
        self.refresh()
        if state == "listening" and not self._dictation_ready:
            self._dictation_ready = True
            self.notify("Dictado activo. Habla para escribir en el campo seleccionado.", "dictation")

    def refresh(self):
        if self._closed:
            return
        items = []
        if self.gestures:
            if self.camera_error:
                text, color = "Cámara no disponible", RED
            else:
                text = "Mano detectada" if self.hand else "Sin mano" if self.camera_ready else "Preparando"
                color = GREEN if self.hand else AMBER
            items.append(("hand", "Gestos · " + text, color))
        if self.dictating:
            text, color = {
                "preparing": ("Preparando", AMBER),
                "listening": ("Escuchando", GREEN),
                "processing": ("Procesando", BLUE),
            }[self.dictation_state]
            items.append(("mic", "Dictado · " + text, color))
        elif self.voice:
            color = GREEN if self.voice_state == "Lista" else RED if self.voice_state == "No disponible" else AMBER
            items.append(("mic", "Voz · " + self.voice_state, color))
        self.indicator.set_items(items)

    def close(self):
        self._closed = True
        self.notice.timer.stop()
        self.notice.close()
        self.indicator.close()
