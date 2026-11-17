"""Acciones discretas de teclado y ratón solicitadas por los reconocedores."""

from enum import StrEnum


class Action(StrEnum):
    """Una acción puntual sobre el campo o la posición que tiene el foco."""

    LEFT_CLICK = "left_click"
    LEFT_DOWN = "left_down"  # inicio del arrastre: presiona sin soltar
    LEFT_UP = "left_up"  # término del arrastre: suelta el botón
    RIGHT_CLICK = "right_click"
    ENTER = "enter"
    DOUBLE_CLICK = "double_click"  # solo lo piden las macros (MOUSE_CLICK)
    SCROLL_UP = "scroll_up"  # un paso de la rueda hacia arriba
    SCROLL_DOWN = "scroll_down"  # un paso de la rueda hacia abajo
