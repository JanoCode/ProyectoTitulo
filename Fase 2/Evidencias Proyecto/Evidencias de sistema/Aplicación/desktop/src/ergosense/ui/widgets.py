"""Componentes reutilizables de la interfaz: botones, interruptor, estados y cámara."""

from itertools import pairwise

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPointF,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    QTimer,
)
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QAbstractButton,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ergosense.gestures.control_area import control_area, cursor_area
from ergosense.ui import icons, theme


def label(text="", role=None, wrap=False):
    """Crea un texto con el estilo indicado por su rol (h1, muted, small...)."""
    widget = QLabel(text)
    if role:
        widget.setProperty("role", role)
    widget.setWordWrap(wrap)
    return widget


def button(text, variant="primary", icon_name=None, icon_color=None):
    """Crea un botón con el estilo indicado: primary, secondary, ghost o link."""
    widget = QPushButton(text)
    widget.setProperty("variant", variant)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    if icon_name:
        color = icon_color or ("white" if variant == "primary" else theme.TEXT)
        widget.setIcon(icons.icon(icon_name, color, 16))
        widget.setIconSize(QSize(16, 16))
    return widget


def restyle(widget):
    """Vuelve a aplicar la hoja de estilos después de cambiar una propiedad."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def divider(vertical=False):
    """Línea fina que separa secciones."""
    line = QFrame()
    line.setObjectName("verticalDivider" if vertical else "divider")
    return line


def icon_label(name, color=theme.TEXT, size=18):
    """Un ícono suelto, como imagen."""
    widget = QLabel()
    widget.setPixmap(icons.pixmap(name, color, size))
    widget.setFixedSize(size, size)
    return widget


class InfoBox(QFrame):
    """Recuadro celeste con un ícono de información y un texto breve."""

    def __init__(self, text, kind="info"):
        super().__init__()
        self.setObjectName("infoBox" if kind == "info" else "noteBox")
        color = theme.INFO_TEXT if kind == "info" else theme.MUTED
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        layout.addWidget(icon_label("info", color, 15), 0, Qt.AlignmentFlag.AlignTop)
        self.text_label = label(text, wrap=True)
        layout.addWidget(self.text_label, 1)


class IconBadge(QLabel):
    """Ícono dentro de un cuadrado gris redondeado, como en los encabezados."""

    def __init__(self, name, size=36, color=theme.TEXT):
        super().__init__()
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setPixmap(icons.pixmap(name, color, size // 2))
        self.setStyleSheet(f"background: {theme.SUBTLE}; border-radius: 6px;")


class ToggleSwitch(QAbstractButton):
    """Interruptor de encendido y apagado, como el de los teléfonos."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(40, 22)
        self._offset = 0.0  # 0: apagado (perilla a la izquierda); 1: encendido
        self._animation = QPropertyAnimation(self, b"offset", self)
        self._animation.setDuration(140)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.toggled.connect(self._animate)

    def _get_offset(self):
        return self._offset

    def _set_offset(self, value):
        self._offset = value
        self.update()

    offset = Property(float, _get_offset, _set_offset)

    def _animate(self, checked):
        self._animation.stop()
        self._animation.setEndValue(1.0 if checked else 0.0)
        self._animation.start()

    def set_checked_silently(self, checked):
        """Cambia el estado sin avisar, para reflejar lo que confirmó el servidor."""
        self.blockSignals(True)
        self.setChecked(checked)
        self.blockSignals(False)
        self._animation.stop()
        self._set_offset(1.0 if checked else 0.0)

    def sizeHint(self):
        return QSize(40, 22)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = QRectF(1, 1, self.width() - 2, self.height() - 2)
        on = QColor(theme.PRIMARY)
        off = QColor("#C7CCD2")
        # Mezcla los colores según la posición, para que la animación sea suave.
        color = QColor(
            int(off.red() + (on.red() - off.red()) * self._offset),
            int(off.green() + (on.green() - off.green()) * self._offset),
            int(off.blue() + (on.blue() - off.blue()) * self._offset),
        )
        if not self.isEnabled():
            color.setAlpha(120)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(track, track.height() / 2, track.height() / 2)
        diameter = track.height() - 6
        x = track.left() + 3 + (track.width() - diameter - 6) * self._offset
        painter.setBrush(QColor("white"))
        painter.drawEllipse(QRectF(x, track.top() + 3, diameter, diameter))


# Color del punto de cada estado.
STATE_COLORS = {
    "off": theme.NEUTRAL,
    "waiting": theme.WARNING,
    "ok": theme.SUCCESS,
    "error": theme.DANGER,
    "info": theme.PRIMARY,
}


class StatusIndicator(QWidget):
    """Punto de color con un texto: gris desactivado, ámbar en espera, verde activo."""

    def __init__(self, text="", state="off", small=False, stretch=True):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        self.dot = QLabel()
        self.dot.setFixedSize(8, 8)
        self.text_label = label(text, "small" if small else "muted")
        layout.addWidget(self.dot)
        layout.addWidget(self.text_label)
        if stretch:
            layout.addStretch()
        self.state = None
        self.set_status(text, state)

    def set_status(self, text, state):
        self.state = state
        self.text_label.setText(text)
        color = STATE_COLORS.get(state, theme.NEUTRAL)
        self.dot.setStyleSheet(f"background: {color}; border-radius: 4px;")

    def text(self):
        return self.text_label.text()


class Toast(QFrame):
    """Mensaje breve que aparece abajo de la ventana y se oculta solo."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("toast")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 11, 18, 11)
        layout.setSpacing(10)
        self._icon = QLabel()
        self._icon.setFixedSize(16, 16)
        self.text_label = QLabel()
        layout.addWidget(self._icon)
        layout.addWidget(self.text_label)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)
        self.hide()

    def show_message(self, text, kind="success", milliseconds=3500):
        name, color = (
            ("check", "#7DD99E") if kind == "success" else ("alert", "#FFB4A9")
        )
        self._icon.setPixmap(icons.pixmap(name, color, 16))
        self.text_label.setText(text)
        self.adjustSize()
        self.reposition()
        self.show()
        self.raise_()
        self._timer.start(milliseconds)

    def reposition(self):
        parent = self.parentWidget()
        if parent is None:
            return
        x = (parent.width() - self.width()) // 2
        y = parent.height() - self.height() - 48  # sobre la barra de estado
        self.move(max(x, 0), max(y, 0))


# Huesos de la mano para dibujar el seguimiento (0 es la muñeca).
HAND_CHAINS = [
    [0, 1, 2, 3, 4],
    [0, 5, 6, 7, 8],
    [9, 10, 11, 12],
    [13, 14, 15, 16],
    [0, 17, 18, 19, 20],
    [5, 9, 13, 17],
]


class CameraView(QWidget):
    """Imagen de la cámara con el seguimiento de la mano y las etiquetas encima."""

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(320, 240)
        self._image = None
        self._points = None
        self.show_tracking = True
        self.gesture_text = ""
        self.control_side = "right"

    def set_frame(self, image, points):
        """Recibe un cuadro (QImage) y los puntos de la mano entre 0 y 1, o None."""
        self._image = image
        self._points = points
        self.update()

    def clear(self):
        self._image = None
        self._points = None
        self.gesture_text = ""
        self.update()

    def has_frame(self):
        return self._image is not None

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        area = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        clip = QPainterPath()
        clip.addRoundedRect(area, 8, 8)
        painter.setClipPath(clip)
        painter.fillRect(area, QColor("#1B1E22"))
        if self._image is None or self._image.isNull():
            return

        # La imagen completa conserva sus proporciones para no ocultar el área activa.
        scale = min(
            area.width() / self._image.width(), area.height() / self._image.height()
        )
        width, height = self._image.width() * scale, self._image.height() * scale
        left = area.left() + (area.width() - width) / 2
        top = area.top() + (area.height() - height) / 2
        painter.drawImage(QRectF(left, top, width, height), self._image)
        x1, y1, x2, y2 = control_area(
            self.control_side, (self._image.width(), self._image.height())
        )
        active = QRectF(left + x1 * width, top + y1 * height,
                       (x2 - x1) * width, (y2 - y1) * height)
        outside = QPainterPath()
        outside.addRect(QRectF(left, top, width, height))
        inside = QPainterPath()
        inside.addRect(active)
        painter.fillPath(outside.subtracted(inside), QColor(0, 0, 0, 75))
        painter.setPen(QPen(QColor(theme.PRIMARY), 2, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(active, 8, 8)
        a, b, c, d = cursor_area((x1, y1, x2, y2))
        travel = QRectF(left + a * width, top + b * height, (c-a)*width, (d-b)*height)
        painter.setPen(QPen(QColor("white"), 1.5, Qt.PenStyle.DotLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(travel)
        self._draw_badge(
            painter, QPointF(active.left(), max(area.top() + 8, active.top() - 34)),
            "Área de acción",
        )

        if self.show_tracking and self._points:
            points = [
                QPointF(left + x * width, top + y * height) for x, y in self._points
            ]
            painter.setPen(QPen(QColor(89, 160, 240), 2))
            for chain in HAND_CHAINS:
                for a, b in pairwise(chain):
                    painter.drawLine(points[a], points[b])
            painter.setPen(QPen(QColor(theme.PRIMARY), 1.5))
            painter.setBrush(QColor("white"))
            for point in points:
                painter.drawEllipse(point, 3.2, 3.2)

        painter.setClipping(False)
        self._draw_badge(painter, QPointF(12, 12), "En vivo", dot=theme.SUCCESS)
        if self.gesture_text:
            self._draw_badge(
                painter,
                QPointF(12, self.height() - 42),
                self.gesture_text,
                icon_name="hand",
            )

    def _draw_badge(self, painter, origin, text, dot=None, icon_name=None):
        metrics = painter.fontMetrics()
        lead = 18 if (dot or icon_name) else 0
        rect = QRectF(
            origin.x(), origin.y(), metrics.horizontalAdvance(text) + lead + 20, 30
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(20, 22, 26, 200))
        painter.drawRoundedRect(rect, 5, 5)
        if dot:
            painter.setBrush(QColor(dot))
            painter.drawEllipse(QPointF(rect.left() + 14, rect.center().y()), 3.5, 3.5)
        if icon_name:
            painter.drawPixmap(
                int(rect.left() + 8),
                int(rect.center().y() - 7),
                icons.pixmap(icon_name, "white", 14),
            )
        painter.setPen(QColor("white"))
        painter.drawText(
            rect.adjusted(10 + lead, 0, -8, 0),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            text,
        )


class CameraPlaceholder(QFrame):
    """Lo que se muestra cuando no hay imagen: cámara apagada, iniciándose o ausente."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            f"CameraPlaceholder {{ background: {theme.SUBTLE}; border: 1px solid {theme.BORDER};"
            " border-radius: 8px; }"
        )
        layout = QVBoxLayout(self)
        layout.addStretch()
        self.badge = QLabel()
        self.badge.setFixedSize(60, 60)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setStyleSheet("background: #DCE0E5; border-radius: 30px;")
        self.title = label("", "placeholderTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text = label("", "muted", wrap=True)
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Ancho fijo: un texto con saltos de línea y centrado no calcula bien el suyo.
        self.text.setFixedWidth(380)
        self.action = button("", "primary")
        for widget in (self.badge, self.title, self.text, self.action):
            layout.addWidget(widget, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.setSpacing(10)
        layout.addStretch()

    def set_content(
        self, icon_name, title, text, action_text=None, icon_name_action=None
    ):
        self.badge.setPixmap(icons.pixmap(icon_name, theme.MUTED, 28))
        self.title.setText(title)
        self.text.setText(text)
        # Alto justo para todas las líneas del texto, que si no se corta.
        self.text.setFixedHeight(self.text.heightForWidth(self.text.width()))
        self.action.setVisible(bool(action_text))
        if action_text:
            self.action.setText(action_text)
            if icon_name_action:
                self.action.setIcon(icons.icon(icon_name_action, "white", 16))
