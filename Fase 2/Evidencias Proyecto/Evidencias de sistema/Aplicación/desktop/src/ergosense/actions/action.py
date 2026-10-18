"""Acciones discretas del mouse que pueden pedir los gestos y, más adelante, la voz."""

from enum import StrEnum


class Action(StrEnum):
    """Una acción puntual sobre el mouse, en la posición actual del cursor."""

    LEFT_CLICK = "left_click"
    LEFT_DOWN = "left_down"  # inicio del arrastre: presiona sin soltar
    LEFT_UP = "left_up"  # término del arrastre: suelta el botón
    RIGHT_CLICK = "right_click"
    SCROLL_UP = "scroll_up"  # un paso de la rueda hacia arriba
    SCROLL_DOWN = "scroll_down"  # un paso de la rueda hacia abajo
