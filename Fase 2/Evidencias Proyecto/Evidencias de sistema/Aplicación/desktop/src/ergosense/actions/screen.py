"""Tamaño del monitor principal de Windows, donde se mueve el cursor de los gestos."""

import ctypes

SM_CXSCREEN = 0  # ancho del monitor principal
SM_CYSCREEN = 1  # alto del monitor principal


def primary_screen():
    """Devuelve (izquierda, arriba, ancho, alto) del monitor principal, en píxeles."""
    user32 = ctypes.windll.user32
    width = user32.GetSystemMetrics(SM_CXSCREEN)
    height = user32.GetSystemMetrics(SM_CYSCREEN)
    # El monitor principal siempre empieza en (0, 0); los otros se ubican a su lado.
    return (0, 0, width, height)
