"""Colores, tipografía y hoja de estilos de la interfaz (Sprint 04: PB-17 a PB-20).

Todos los colores están aquí, con nombre, para que la interfaz sea coherente y se
pueda ajustar en un solo lugar. Los componentes eligen su estilo con propiedades
de Qt: por ejemplo, un botón con variant="primary" se ve como el botón principal.
"""

from PySide6.QtGui import QFont

PRIMARY = "#1667C2"
PRIMARY_HOVER = "#125BAD"
PRIMARY_PRESSED = "#0E4D93"
TEXT = "#1F2328"
MUTED = "#5B6570"
BORDER = "#DDE1E6"
SURFACE = "#FFFFFF"
SIDEBAR = "#F6F7F9"
SUBTLE = "#EEF1F4"
SUCCESS = "#2E9D5B"
WARNING = "#C98A1B"
DANGER = "#C62828"
NEUTRAL = "#8A939D"
INFO_BG = "#E9F2FC"
INFO_TEXT = "#24496F"
TOAST_BG = "#2B2F33"
FONT_FAMILY = "Segoe UI"

STYLE_SHEET = f"""
QWidget {{
    color: {TEXT};
    font-family: "{FONT_FAMILY}";
    font-size: 10pt;
}}
QWidget#window, QDialog {{
    background: {SURFACE};
}}

/* Encabezado, panel lateral y barra de estado */
QFrame#header {{
    background: {SURFACE};
    border-bottom: 1px solid {BORDER};
}}
QFrame#sidebar {{
    background: {SIDEBAR};
    border-left: 1px solid {BORDER};
}}
QFrame#statusBar {{
    background: {SURFACE};
    border-top: 1px solid {BORDER};
}}
QFrame#divider {{
    background: {BORDER};
    max-height: 1px;
    min-height: 1px;
}}
QFrame#verticalDivider {{
    background: {BORDER};
    max-width: 1px;
    min-width: 1px;
}}

/* Textos */
QLabel[role="brand"] {{ font-size: 12pt; font-weight: 600; }}
QLabel[role="h1"] {{ font-size: 15pt; font-weight: 600; }}
QLabel[role="h2"] {{ font-size: 11pt; font-weight: 600; }}
QLabel[role="dialogTitle"] {{ font-size: 13pt; font-weight: 600; }}
QLabel[role="loginTitle"] {{ font-size: 17pt; font-weight: 600; }}
QLabel[role="muted"] {{ color: {MUTED}; }}
QLabel[role="small"] {{ color: {MUTED}; font-size: 9pt; }}
QLabel[role="timer"] {{ font-size: 24pt; font-weight: 600; }}
QLabel[role="fieldLabel"] {{ font-weight: 600; }}
QLabel[role="fieldError"] {{ color: {DANGER}; font-size: 9pt; }}
QLabel[role="formError"] {{ color: {DANGER}; }}
QLabel[role="formSuccess"] {{ color: {SUCCESS}; }}
QLabel[role="placeholderTitle"] {{ font-size: 12pt; }}

/* Cuadro de información */
QFrame#infoBox {{
    background: {INFO_BG};
    border-radius: 6px;
}}
QFrame#infoBox QLabel {{ color: {INFO_TEXT}; font-size: 9pt; }}
QFrame#noteBox {{
    background: {SUBTLE};
    border-radius: 6px;
}}
QFrame#noteBox QLabel {{ color: {MUTED}; font-size: 9pt; }}

/* Botones */
QPushButton {{
    border-radius: 4px;
    padding: 7px 16px;
    font-weight: 600;
}}
QPushButton[variant="primary"] {{
    background: {PRIMARY};
    color: white;
    border: 1px solid {PRIMARY};
}}
QPushButton[variant="primary"]:hover {{ background: {PRIMARY_HOVER}; }}
QPushButton[variant="primary"]:pressed {{ background: {PRIMARY_PRESSED}; }}
QPushButton[variant="primary"]:disabled {{
    background: #9DBCE3;
    border-color: #9DBCE3;
}}
QPushButton[variant="secondary"] {{
    background: {SURFACE};
    color: {TEXT};
    border: 1px solid #B9C0C8;
}}
QPushButton[variant="secondary"]:hover {{ background: {SUBTLE}; }}
QPushButton[variant="ghost"] {{
    background: transparent;
    border: 1px solid transparent;
    font-weight: 400;
    padding: 6px 10px;
}}
QPushButton[variant="ghost"]:hover {{
    background: {SUBTLE};
    border-color: {BORDER};
}}
QPushButton[variant="link"] {{
    background: transparent;
    color: {PRIMARY};
    border: none;
    padding: 2px 0;
}}
QPushButton[variant="link"]:hover {{ text-decoration: underline; }}
QPushButton[variant="icon"] {{
    background: transparent;
    border: none;
    padding: 4px;
}}
QPushButton[variant="icon"]:hover {{ background: {SUBTLE}; }}
QToolButton#userButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 8px;
}}
QToolButton#userButton:hover {{
    background: {SUBTLE};
    border-color: {BORDER};
}}
QToolButton#userButton::menu-indicator {{ image: none; width: 0; }}

/* Campos */
QLineEdit, QSpinBox {{
    background: {SURFACE};
    border: 1px solid #B9C0C8;
    border-radius: 4px;
    padding: 7px 10px;
    selection-background-color: {PRIMARY};
}}
QLineEdit:focus, QSpinBox:focus {{ border: 2px solid {PRIMARY}; padding: 6px 9px; }}
QLineEdit[invalid="true"] {{ border: 1px solid {DANGER}; }}
QSpinBox::up-button, QSpinBox::down-button {{ width: 18px; border: none; }}
QCheckBox {{ spacing: 8px; color: {MUTED}; }}
QCheckBox::indicator {{
    width: 15px;
    height: 15px;
    border: 1px solid #9AA3AD;
    border-radius: 3px;
    background: {SURFACE};
}}
QCheckBox::indicator:checked {{
    background: {PRIMARY};
    border-color: {PRIMARY};
    image: url(":/ergosense/check-white.svg");
}}

/* Pestañas de la ayuda */
QTabWidget::pane {{ border: none; border-top: 1px solid {BORDER}; }}
QTabBar::tab {{
    background: transparent;
    border: none;
    padding: 9px 14px;
    color: {TEXT};
}}
QTabBar::tab:selected {{
    color: {PRIMARY};
    border-bottom: 2px solid {PRIMARY};
}}
QTabBar::tab:hover:!selected {{ color: {PRIMARY_HOVER}; }}

/* Menú de la cuenta */
QMenu {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 0;
}}
QMenu::item {{ padding: 8px 18px; }}
QMenu::item:selected {{ background: {SUBTLE}; color: {TEXT}; }}
QMenu::separator {{ height: 1px; background: {BORDER}; margin: 4px 0; }}

/* Notificación breve */
QFrame#toast {{
    background: {TOAST_BG};
    border-radius: 6px;
}}
QFrame#toast QLabel {{ color: white; }}
"""


CHECK_ICON_PLACEHOLDER = ":/ergosense/check-white.svg"


def apply_theme(app):
    """Aplica la tipografía y la hoja de estilos a toda la aplicación."""
    # Se importa aquí porque icons también usa los colores de este archivo.
    from ergosense.ui.icons import write_icon_file

    app.setFont(QFont(FONT_FAMILY, 10))
    # La marca de las casillas es un SVG; la hoja de estilos necesita su ruta.
    check = write_icon_file("check", "#FFFFFF")
    app.setStyleSheet(STYLE_SHEET.replace(CHECK_ICON_PLACEHOLDER, check))
