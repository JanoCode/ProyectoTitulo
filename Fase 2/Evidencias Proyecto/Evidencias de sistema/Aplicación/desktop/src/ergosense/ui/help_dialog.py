"""Ayuda con los gestos y los comandos de voz disponibles (PB-08 y PB-16).

La lista de comandos sale del mismo vocabulario que usa el reconocimiento de voz,
así que la ayuda nunca muestra un comando que no exista.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ergosense.ui import theme
from ergosense.ui.widgets import IconBadge, InfoBox, button, divider, icon_label, label
from ergosense.voice.commands import COMMANDS

# Los gestos que reconoce el clasificador (ergosense.gestures.classifier).
GESTURES = [
    ("Mano abierta", "Mover el cursor"),
    ("Pulgar adentro", "Clic izquierdo"),
    ("Índice abajo", "Clic derecho"),
    ("Dos dedos extendidos", "Desplazamiento vertical"),
    ("Mantener el pulgar adentro y mover", "Arrastrar"),
    ("Abrir el pulgar", "Soltar"),
    # Sin acción predefinida: el usuario los asigna a sus macros (Sprint 05).
    ("Puño", "Activar una macro"),
    ("L (índice y pulgar)", "Activar una macro"),
]
GESTURES_TAB, VOICE_TAB = 0, 1


def _fill_grid(grid, items):
    """Ubica los elementos en dos columnas, con una línea bajo cada fila."""
    for index, item in enumerate(items):
        row, column = divmod(index, 2)
        item.setContentsMargins(4, 10, 4, 10)
        grid.addWidget(item, row * 2, column)
        if column == 0:
            grid.addWidget(divider(), row * 2 + 1, 0, 1, 2)


def _gesture_item(title, action):
    item = QWidget()
    row = QHBoxLayout(item)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(12)
    row.addWidget(IconBadge("hand", 44, theme.PRIMARY))
    text = QVBoxLayout()
    text.setSpacing(2)
    text.addWidget(label(title, "fieldLabel"))
    text.addWidget(label(action, "muted"))
    row.addLayout(text, 1)
    return item


def _command_item(phrase):
    item = QWidget()
    row = QHBoxLayout(item)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(10)
    row.addWidget(icon_label("mic", theme.MUTED, 15))
    row.addWidget(label(f"“{phrase[0].upper()}{phrase[1:]}”"), 1)
    return item


class HelpDialog(QDialog):
    """Ventana de ayuda con una pestaña para gestos y otra para comandos de voz."""

    def __init__(self, parent=None, tab=GESTURES_TAB):
        super().__init__(parent)
        self.setWindowTitle("Ayuda")
        self.setMinimumWidth(600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        header = QVBoxLayout()
        header.setContentsMargins(22, 18, 22, 6)
        header.addWidget(label("Ayuda", "dialogTitle"))
        layout.addLayout(header)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self._gestures_page(), "Gestos")
        self.tabs.addTab(self._commands_page(), "Comandos de voz")
        self.tabs.setCurrentIndex(tab)
        layout.addWidget(self.tabs)

        layout.addWidget(divider())
        footer = QHBoxLayout()
        footer.setContentsMargins(22, 14, 22, 14)
        footer.addStretch()
        close = button("Cerrar", "primary")
        close.clicked.connect(self.accept)
        footer.addWidget(close)
        layout.addLayout(footer)

    def _gestures_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(22, 16, 22, 12)
        intro = label(
            "Los gestos solo ejecutan acciones cuando <b>Control con la mano</b> está "
            "activado. Hazlos con la palma de frente a la cámara.",
            "muted",
            wrap=True,
        )
        intro.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(intro)
        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(0)
        _fill_grid(grid, [_gesture_item(title, action) for title, action in GESTURES])
        layout.addLayout(grid)
        layout.addStretch()
        return page

    def _commands_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(22, 16, 22, 12)
        layout.addWidget(
            label(
                "Estos comandos son predefinidos. Di una frase tal como aparece en la lista.",
                "muted",
                wrap=True,
            )
        )
        box = QFrame()
        box.setStyleSheet(
            f"QFrame#commands {{ border: 1px solid {theme.BORDER}; "
            "border-radius: 6px; }"
        )
        box.setObjectName("commands")
        grid = QGridLayout(box)
        grid.setContentsMargins(10, 0, 10, 0)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(0)
        _fill_grid(grid, [_command_item(phrase) for phrase in COMMANDS])
        layout.addWidget(box)
        layout.addSpacing(8)
        layout.addWidget(
            InfoBox(
                "Cuando el micrófono está apagado, activa de nuevo la voz mediante el "
                "interruptor de la ventana principal."
            )
        )
        layout.addStretch()
        return page
