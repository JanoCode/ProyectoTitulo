"""Pruebas del adaptador del mouse (Sprint 03: PB-09 a PB-12)."""

import pytest
from pynput.mouse import Button

from ergosense.actions.action import Action
from ergosense.actions.mouse import MouseActions


class FakeController:
    """Mouse falso: anota lo que se le pide en vez de moverse."""

    def __init__(self):
        self.position = (0, 0)
        self.calls = []

    def click(self, button, count=1):
        self.calls.append(("click", button))

    def press(self, button):
        self.calls.append(("press", button))

    def release(self, button):
        self.calls.append(("release", button))

    def scroll(self, dx, dy):
        self.calls.append(("scroll", dy))


def test_mueve_el_cursor():
    controller = FakeController()
    MouseActions(controller).move((100, 200))
    assert controller.position == (100, 200)


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        (Action.LEFT_CLICK, ("click", Button.left)),
        (Action.LEFT_DOWN, ("press", Button.left)),
        (Action.LEFT_UP, ("release", Button.left)),
        (Action.RIGHT_CLICK, ("click", Button.right)),
        (Action.SCROLL_UP, ("scroll", 1)),
        (Action.SCROLL_DOWN, ("scroll", -1)),
    ],
)
def test_cada_accion_usa_el_boton_correcto(action, expected):
    controller = FakeController()
    MouseActions(controller).perform(action)
    assert controller.calls == [expected]
