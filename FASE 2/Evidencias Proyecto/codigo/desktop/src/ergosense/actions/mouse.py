"""Adaptador del mouse del sistema operativo, basado en pynput (PB-09 a PB-12)."""

from pynput.mouse import Button, Controller

from ergosense.actions.action import Action


class MouseActions:
    """Mueve el cursor y ejecuta clicks, arrastres y scroll en Windows."""

    def __init__(self, controller=None):
        # En las pruebas se entrega un controlador falso; en la app, el de pynput.
        self._mouse = controller if controller is not None else Controller()

    def move(self, position):
        """Lleva el cursor a la posición (x, y) de la pantalla."""
        self._mouse.position = position

    def perform(self, action):
        """Ejecuta una acción en la posición actual del cursor."""
        if action is Action.LEFT_CLICK:
            self._mouse.click(Button.left)
        elif action is Action.LEFT_DOWN:
            self._mouse.press(Button.left)
        elif action is Action.LEFT_UP:
            self._mouse.release(Button.left)
        elif action is Action.RIGHT_CLICK:
            self._mouse.click(Button.right)
        elif action is Action.SCROLL_UP:
            self._mouse.scroll(0, 1)  # dy positivo: la rueda hacia arriba
        elif action is Action.SCROLL_DOWN:
            self._mouse.scroll(0, -1)
