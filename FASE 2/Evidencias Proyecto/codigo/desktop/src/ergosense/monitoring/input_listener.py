"""Escucha global de teclado y mouse (PB-02 y PB-03).

Solo informa que hubo actividad: nunca guarda qué tecla o botón se usó (RNF-16).
"""

from pynput import keyboard, mouse


class InputListener:
    """Escucha el teclado y el mouse del sistema y avisa cada interacción."""

    def __init__(self, on_activity):
        # Función sin parámetros que se llama en cada interacción, p. ej. recorder.register.
        self._on_activity = on_activity
        self._keyboard = None
        self._mouse = None

    def start(self):
        """Comienza a escuchar en hilos propios de pynput."""
        self._keyboard = keyboard.Listener(on_press=self._on_press)
        self._mouse = mouse.Listener(on_click=self._on_click)
        self._keyboard.start()
        self._mouse.start()

    def stop(self):
        """Deja de escuchar el teclado y el mouse."""
        if self._keyboard is not None:
            self._keyboard.stop()
        if self._mouse is not None:
            self._mouse.stop()

    def _on_press(self, _key, _injected=False):
        """Avisa que hubo actividad al presionar una tecla, sin usar cuál fue."""
        self._on_activity()

    def _on_click(self, _x, _y, _button, pressed, _injected=False):
        """Avisa que hubo actividad solo al presionar un botón, no al soltarlo."""
        if pressed:
            self._on_activity()
