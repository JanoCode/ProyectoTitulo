"""Ejecución de cada tipo de acción de las macros (PB-42; arquitectura, 5.5).

El ejecutor único de acciones llama a ActionRunner.perform, en su propio hilo, con
las acciones del mouse de los gestos y la voz y con los pasos de las macros. Así,
un gesto, un comando y una macro nunca se intercalan.
"""

import subprocess
import webbrowser
from dataclasses import dataclass
from pathlib import Path

from pynput.keyboard import Controller, Key

from ergosense.actions.action import Action

CLICKS = {
    "left": Action.LEFT_CLICK,
    "right": Action.RIGHT_CLICK,
    "double": Action.DOUBLE_CLICK,
}
KEYS = {
    "ctrl": Key.ctrl,
    "shift": Key.shift,
    "alt": Key.alt,
    "win": Key.cmd,
    "enter": Key.enter,
    "esc": Key.esc,
    "tab": Key.tab,
    "space": Key.space,
    "backspace": Key.backspace,
    "delete": Key.delete,
    "insert": Key.insert,
    "home": Key.home,
    "end": Key.end,
    "pageup": Key.page_up,
    "pagedown": Key.page_down,
    "up": Key.up,
    "down": Key.down,
    "left": Key.left,
    "right": Key.right,
    **{f"f{number}": getattr(Key, f"f{number}") for number in range(1, 13)},
}


@dataclass(frozen=True)
class MacroStep:
    """Una acción de una macro. En OPEN_APP, value ya es la ruta en este equipo."""

    action_type: str
    value: str
    macro_name: str = ""


class ActionRunner:
    def __init__(
        self,
        mouse,
        keyboard=None,
        open_url=webbrowser.open,
        start_process=subprocess.Popen,
        on_error=None,
    ):
        # En las pruebas se entregan un teclado, un navegador y un proceso falsos.
        self._mouse = mouse
        self._keyboard = keyboard if keyboard is not None else Controller()
        self._open_url = open_url
        self._start_process = start_process
        self._on_error = on_error or (lambda message: None)

    def perform(self, action):
        if not isinstance(action, MacroStep):
            self._mouse.perform(action)  # click, arrastre o scroll de gestos y voz
            return
        try:
            self._run(action)
        except OSError:
            # Por ejemplo, la aplicación se desinstaló. El hilo de acciones sigue.
            self._on_error(
                f"La macro «{action.macro_name}» no pudo abrir {action.value}."
            )

    def _run(self, step):
        kind, value = step.action_type, step.value
        if kind == "OPEN_URL":
            self._open_url(value)
        elif kind == "OPEN_APP":
            self._start_process([value], cwd=str(Path(value).parent))
        elif kind == "KEY_PRESS":
            self._press(value)
        elif kind == "TYPE_TEXT":
            self._keyboard.type(value)
        elif kind == "MOUSE_CLICK":
            self._mouse.perform(CLICKS[value])

    def _press(self, combination):
        """Presiona los modificadores, la tecla final y los suelta en orden inverso."""
        *modifiers, key = combination.lower().split("+")
        held = [KEYS[name] for name in modifiers]
        final = KEYS.get(key, key)
        pressed = []
        try:
            for modifier in held:
                self._keyboard.press(modifier)
                pressed.append(modifier)
            self._keyboard.press(final)
            pressed.append(final)
            self._keyboard.release(final)
            pressed.pop()
        finally:
            # Nunca queda una tecla presionada, aunque algo falle.
            for key in reversed(pressed):
                try:
                    self._keyboard.release(key)
                except OSError:
                    pass
