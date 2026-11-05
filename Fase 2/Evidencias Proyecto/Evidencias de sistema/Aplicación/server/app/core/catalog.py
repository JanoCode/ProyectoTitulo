"""Catálogo compartido de comandos de voz, gestos y acciones (arquitectura, 5.4 y 5.5).

Es el mismo catálogo de la aplicación de escritorio (ergosense/macros/catalog.py).
La API lo usa para validar los activadores y las acciones de las macros, ya que es
la fuente de verdad (PB-40 y PB-44).
"""

import re
import string
import unicodedata
from urllib.parse import urlsplit

# Comandos de voz base del Sprint 04: una macro no puede usar estas frases.
BASE_VOICE_COMMANDS = frozenset(
    {
        "clic izquierdo",
        "clic derecho",
        "subir",
        "bajar",
        "activar gestos",
        "desactivar gestos",
        "activar voz",
        "desactivar voz",
        "activar gestos y voz",
        "desactivar gestos y voz",
    }
)
# Gestos del Sprint 03: los que tienen una acción predefinida no sirven de activador.
GESTURES_WITH_ACTION = frozenset({"point", "thumb_in", "index_down", "two_fingers"})
MACRO_GESTURES = frozenset({"fist", "l_shape"})

TRIGGER_TYPES = ("VOICE", "GESTURE")
ACTION_TYPES = ("OPEN_URL", "OPEN_APP", "KEY_PRESS", "TYPE_TEXT", "MOUSE_CLICK")
MOUSE_BUTTONS = frozenset({"left", "right", "double"})
MODIFIER_KEYS = frozenset({"ctrl", "shift", "alt", "win"})
NAMED_KEYS = frozenset(
    {
        "enter",
        "esc",
        "tab",
        "space",
        "backspace",
        "delete",
        "insert",
        "home",
        "end",
        "pageup",
        "pagedown",
        "up",
        "down",
        "left",
        "right",
        *(f"f{number}" for number in range(1, 13)),
    }
)
SINGLE_KEYS = frozenset(string.ascii_lowercase + string.digits)
MAX_PHRASE_LENGTH = 60
MAX_TEXT_LENGTH = 500
_PHRASE = re.compile(r"[a-záéíóúüñ ]+")


def clean_phrase(text: str) -> str:
    """Forma guardada de una frase: minúsculas y espacios simples, con tildes."""
    return " ".join(text.lower().split())


def normalize_phrase(text: str) -> str:
    """Forma para comparar frases: además, sin tildes (arquitectura, 5.5)."""
    without_accents = "".join(
        char
        for char in unicodedata.normalize("NFD", text.casefold())
        if unicodedata.category(char) != "Mn"
    )
    return " ".join(without_accents.split())


def trigger_error(trigger_type: str, value: str) -> str | None:
    """Motivo por el que un activador no es válido, o None si lo es."""
    if trigger_type == "VOICE":
        phrase = clean_phrase(value)
        if not phrase or len(phrase) > MAX_PHRASE_LENGTH:
            return f"La frase debe tener entre 1 y {MAX_PHRASE_LENGTH} caracteres."
        if not _PHRASE.fullmatch(phrase):
            return "La frase solo puede tener letras y espacios."
        return None
    if value not in MACRO_GESTURES | GESTURES_WITH_ACTION:
        return "El gesto no es reconocido por ErgoSense."
    return None


def trigger_conflict(trigger_type: str, value: str) -> str | None:
    """Conflicto con un comando de voz base o un gesto predefinido (PB-44)."""
    if trigger_type == "VOICE":
        if normalize_phrase(value) in BASE_VOICE_COMMANDS:
            return f"«{clean_phrase(value)}» es un comando de voz de ErgoSense."
        return None
    if value in GESTURES_WITH_ACTION:
        return "Ese gesto ya tiene una acción predefinida."
    return None


def valid_key_combination(value: str) -> bool:
    """Teclas unidas con +, por ejemplo ctrl+shift+t: modificadores y una tecla final."""
    parts = value.lower().split("+")
    *modifiers, key = parts
    return (
        all(part in MODIFIER_KEYS for part in modifiers)
        and len(set(modifiers)) == len(modifiers)
        and (key in NAMED_KEYS or key in SINGLE_KEYS)
    )


def action_error(action_type: str, value: str) -> str | None:
    """Motivo por el que el valor no sirve para el tipo de acción, o None."""
    if action_type == "OPEN_URL":
        url = urlsplit(value.strip())
        if url.scheme not in ("http", "https") or not url.netloc:
            return "La URL debe comenzar con http:// o https://."
    elif action_type == "OPEN_APP":
        if not value.strip():
            return "Elige una aplicación registrada."
    elif action_type == "KEY_PRESS":
        if not valid_key_combination(value.strip()):
            return "Escribe una combinación válida, por ejemplo ctrl+shift+t."
    elif action_type == "TYPE_TEXT":
        if not value.strip() or len(value) > MAX_TEXT_LENGTH:
            return f"Escribe un texto de hasta {MAX_TEXT_LENGTH} caracteres."
    elif value not in MOUSE_BUTTONS:
        return "Elige click izquierdo, click derecho o doble click."
    return None
