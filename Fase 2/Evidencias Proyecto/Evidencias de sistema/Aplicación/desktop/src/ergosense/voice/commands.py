"""Vocabulario cerrado: cada frase completa corresponde a una sola acción."""

import unicodedata
from types import MappingProxyType

from ergosense.actions.action import Action

COMMANDS = MappingProxyType(
    {
        "clic izquierdo": Action.LEFT_CLICK,
        "clic derecho": Action.RIGHT_CLICK,
        "subir": Action.SCROLL_UP,
        "bajar": Action.SCROLL_DOWN,
        "activar gestos": "gestures_on",
        "desactivar gestos": "gestures_off",
        "activar voz": "voice_on",
        "desactivar voz": "voice_off",
        "activar gestos y voz": "both_on",
        "desactivar gestos y voz": "both_off",
    }
)


def resolve_command(text):
    """Descarta frases parciales, palabras adicionales y expresiones similares."""
    normalized = "".join(
        char
        for char in unicodedata.normalize("NFD", text.casefold())
        if unicodedata.category(char) != "Mn"
    )
    return COMMANDS.get(" ".join(normalized.split()))
