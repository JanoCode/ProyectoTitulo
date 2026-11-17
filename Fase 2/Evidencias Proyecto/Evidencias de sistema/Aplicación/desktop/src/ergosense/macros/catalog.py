"""Catálogo compartido de comandos de voz, gestos y acciones (arquitectura, 5.4 y 5.5).

Es el mismo catálogo de la API (server/app/core/catalog.py). La interfaz lo usa
para informar un problema de inmediato, antes de guardar; la API vuelve a validar,
porque es la fuente de verdad (PB-40 y PB-44).
"""

import re
import string
from urllib.parse import urlsplit

from ergosense.gestures.classifier import Gesture
from ergosense.voice.commands import COMMANDS, normalize

BASE_VOICE_COMMANDS = frozenset(COMMANDS)
# Gestos del Sprint 03: los que tienen una acción predefinida no sirven de activador.
GESTURES_WITH_ACTION = frozenset(
    {Gesture.POINT, Gesture.THUMB_IN, Gesture.INDEX_DOWN, Gesture.TWO_FINGERS}
)
MACRO_GESTURES = (Gesture.FIST, Gesture.L_SHAPE)
GESTURE_NAMES = {Gesture.FIST: "Puño", Gesture.L_SHAPE: "L (índice y pulgar)"}

ACTION_TYPES = ("OPEN_URL", "OPEN_APP", "KEY_PRESS", "TYPE_TEXT", "MOUSE_CLICK")
ACTION_NAMES = {
    "OPEN_URL": "Abrir URL",
    "OPEN_APP": "Abrir aplicación",
    "KEY_PRESS": "Presionar teclas",
    "TYPE_TEXT": "Escribir texto",
    "MOUSE_CLICK": "Hacer click",
}
MOUSE_BUTTONS = {
    "left": "Click izquierdo",
    "right": "Click derecho",
    "double": "Doble click",
}
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


def clean_phrase(text):
    """Forma guardada de una frase: minúsculas y espacios simples, con tildes."""
    return " ".join(text.lower().split())


def trigger_problem(trigger_type, value):
    """Motivo por el que no se puede usar el activador, o None (PB-39 y PB-44)."""
    if trigger_type == "VOICE":
        phrase = clean_phrase(value)
        if not phrase or len(phrase) > MAX_PHRASE_LENGTH:
            return f"La frase debe tener entre 1 y {MAX_PHRASE_LENGTH} caracteres."
        if not _PHRASE.fullmatch(phrase):
            return "La frase solo puede tener letras y espacios."
        if normalize(phrase) in BASE_VOICE_COMMANDS:
            return f"«{phrase}» es un comando de voz de ErgoSense."
        return None
    if value in GESTURES_WITH_ACTION:
        return "Ese gesto ya tiene una acción predefinida."
    if value not in MACRO_GESTURES:
        return "El gesto no es reconocido por ErgoSense."
    return None


def valid_key_combination(value):
    """Teclas unidas con +, por ejemplo ctrl+shift+t: modificadores y una tecla final."""
    *modifiers, key = value.lower().split("+")
    return (
        all(part in MODIFIER_KEYS for part in modifiers)
        and len(set(modifiers)) == len(modifiers)
        and (key in NAMED_KEYS or key in SINGLE_KEYS)
    )


def action_problem(action_type, value):
    """Motivo por el que el valor no sirve para el tipo de acción, o None (PB-40)."""
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
    elif action_type == "MOUSE_CLICK":
        if value not in MOUSE_BUTTONS:
            return "Elige click izquierdo, click derecho o doble click."
    else:
        return "Tipo de acción no soportado."
    return None
