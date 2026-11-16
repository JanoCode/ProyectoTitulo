from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QApplication, QWidget

from ergosense.ui import icons

COLORS = {
    "preparing": "#E6B54A",
    "listening": "#53DAA1",
    "processing": "#78B8FF",
}


class DictationIndicator(QWidget):
    def __init__(self):
        super().__init__(None,
            Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.WindowDoesNotAcceptFocus,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedSize(44, 44)
        self.setWindowOpacity(0.82)
        self.setWindowTitle("Dictado de ErgoSense")
        self._state = "preparing"

    def set_active(self, active):
        if active:
            self.set_state("preparing")
            screen = QApplication.screenAt(self._cursor_position())
            screen = screen or QApplication.primaryScreen()
            if screen is not None:
                area = screen.availableGeometry()
                self.move(area.right() - self.width() - 20, area.top() + 20)
            self.show()
        else:
            self.hide()

    def _cursor_position(self):
        from PySide6.QtGui import QCursor
        return QCursor.pos()

    def set_state(self, state):
        if state in COLORS:
            self._state = state
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(24, 31, 43, 215))
        painter.drawEllipse(QRectF(1, 1, 42, 42))
        painter.drawPixmap(10, 10, icons.pixmap("mic", COLORS[self._state], 24))
