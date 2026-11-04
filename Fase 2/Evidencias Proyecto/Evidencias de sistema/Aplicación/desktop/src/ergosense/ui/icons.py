"""Íconos de la interfaz, dibujados como SVG dentro del código.

Los trazos usan "currentColor", que se reemplaza por el color pedido. Así un mismo
ícono sirve en gris, en azul o en blanco, y no hay archivos de imagen que mantener.
Los dibujos siguen el estilo de líneas de la colección libre Lucide (licencia ISC).
"""

import tempfile
from pathlib import Path

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from ergosense.ui import theme

_SHAPES = {
    "help": '<circle cx="12" cy="12" r="10"/>'
    '<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
    "settings": '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 '
    "0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 "
    "1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15"
    "-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18"
    "a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0"
    "-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73"
    "l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 "
    '0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "hand": '<path d="M18 11V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2"/>'
    '<path d="M14 10V4a2 2 0 0 0-2-2a2 2 0 0 0-2 2v2"/>'
    '<path d="M10 10.5V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2v8"/>'
    '<path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6'
    'a2 2 0 0 1 2.83-2.82L7 15"/>',
    "mic": '<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>'
    '<path d="M19 10v2a7 7 0 0 1-14 0v-2"/><path d="M12 19v3"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "video": '<path d="m16 13 5.223 3.482a.5.5 0 0 0 .777-.416V7.87a.5.5 0 0 0-.752-.432'
    'L16 10.5"/><rect x="2" y="6" width="14" height="12" rx="2"/>',
    "video-off": '<path d="M10.66 6H14a2 2 0 0 1 2 2v2.5l5.248-3.062A.5.5 0 0 1 22 '
    '7.87v8.196"/><path d="M16 16a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h2"/>'
    '<path d="m2 2 20 20"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "check-circle": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 '
    '1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "wifi": '<path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/>'
    '<path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/>',
    "wifi-off": '<path d="M12 20h.01"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/>'
    '<path d="M5 12.859a10 10 0 0 1 5.17-2.69"/>'
    '<path d="M19 12.859a10 10 0 0 0-2.007-1.523"/>'
    '<path d="M2 8.82a15 15 0 0 1 4.177-2.643"/>'
    '<path d="M22 8.82a15 15 0 0 0-11.288-3.764"/><path d="m2 2 20 20"/>',
    "eye": '<path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 '
    '0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/>',
    "eye-off": '<path d="M10.733 5.076a10.744 10.744 0 0 1 11.205 6.575 1 1 0 0 1 0 .696 '
    '10.747 10.747 0 0 1-1.444 2.49"/><path d="M14.084 14.158a3 3 0 0 1-4.242-4.242"/>'
    '<path d="M17.479 17.499a10.75 10.75 0 0 1-15.417-5.151 1 1 0 0 1 0-.696 10.75 '
    '10.75 0 0 1 4.446-5.143"/><path d="m2 2 20 20"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "log-out": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>'
    '<path d="m16 17 5-5-5-5"/><path d="M21 12H9"/>',
}

# El logo es un cuadrado azul con un documento, dibujado con sus propios colores.
_LOGO = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
    f'<rect x="1" y="1" width="22" height="22" rx="5" fill="{theme.PRIMARY}"/>'
    '<rect x="7" y="5.5" width="10" height="13" rx="1.6" fill="none" stroke="white" '
    'stroke-width="1.6"/><path d="M9.5 9.5h5M9.5 12h5M9.5 14.5h3" stroke="white" '
    'stroke-width="1.6" stroke-linecap="round"/></svg>'
)


def _svg(name, color, stroke_width=2):
    if name == "logo":
        return _LOGO
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" '
        f'stroke-linejoin="round">{_SHAPES[name]}</svg>'
    )


def pixmap(name, color=theme.TEXT, size=18, stroke_width=2):
    """Dibuja el ícono pedido en un QPixmap nítido, también en pantallas con escala."""
    ratio = 2  # se dibuja al doble de resolución para que no se vea borroso
    image = QPixmap(size * ratio, size * ratio)
    image.fill(Qt.GlobalColor.transparent)
    renderer = QSvgRenderer(QByteArray(_svg(name, color, stroke_width).encode()))
    painter = QPainter(image)
    renderer.render(painter, QRectF(0, 0, size * ratio, size * ratio))
    painter.end()
    image.setDevicePixelRatio(ratio)
    return image


def icon(name, color=theme.TEXT, size=18):
    """El mismo dibujo como QIcon, para botones y ventanas."""
    return QIcon(pixmap(name, color, size))


def app_icon():
    """Ícono de la aplicación: ventana, barra de tareas y bandeja de Windows."""
    result = QIcon()
    for size in (16, 24, 32, 48, 64):
        result.addPixmap(pixmap("logo", size=size))
    return result


def write_icon_file(name, color):
    """Guarda un ícono como archivo SVG temporal, para usarlo en la hoja de estilos."""
    folder = Path(tempfile.gettempdir()) / "ergosense-icons"
    folder.mkdir(exist_ok=True)
    path = folder / f"{name}-{color.lstrip('#')}.svg"
    path.write_text(_svg(name, color, stroke_width=3), encoding="utf-8")
    # Qt espera barras normales en las rutas de la hoja de estilos.
    return path.as_posix()
