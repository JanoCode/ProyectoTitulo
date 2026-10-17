"""Interpretación de los gestos como acciones del mouse (PB-09 a PB-13).

Decide, cuadro a cuadro, si el cursor debe seguir a la mano y qué acciones
ejecutar: click izquierdo, arrastre, click derecho y scroll. Evita activaciones
accidentales exigiendo gestos estables y ejecutando cada click una sola vez.
"""

from dataclasses import dataclass

from ergosense.actions.action import Action
from ergosense.gestures.classifier import Gesture

# Ajustes de activación (SB03-T19).
STABLE_FRAMES = 3  # cuadros seguidos que debe durar un gesto (unos 0,1 s)
HOLD_SECONDS = 0.4  # pellizco más corto: click; más largo: arrastre
SCROLL_STEP = 20  # píxeles de la cámara que debe subir o bajar la mano por paso


class GestureStabilizer:
    """Acepta un gesto nuevo solo si se repite varios cuadros seguidos (PB-13).

    Así, un gesto que aparece en un solo cuadro por un error de detección, o al
    pasar de una pose a otra, no se considera.
    """

    def __init__(self, frames=STABLE_FRAMES):
        self._frames = frames
        self._stable = Gesture.NONE  # gesto aceptado
        self._candidate = Gesture.NONE  # gesto que se está confirmando
        self._count = 0

    def update(self, gesture):
        """Recibe el gesto del cuadro y devuelve el gesto estable."""
        if gesture is self._stable:
            # Volvió al gesto aceptado: se descarta el candidato.
            self._count = 0
        elif gesture is self._candidate:
            self._count += 1
        else:
            self._candidate = gesture
            self._count = 1
        if self._count >= self._frames:
            self._stable = self._candidate
            self._count = 0
        return self._stable


@dataclass(frozen=True)
class Decision:
    """Qué hacer en este cuadro: si el cursor sigue a la mano y qué acciones ejecutar."""

    move_cursor: bool
    actions: tuple[Action, ...] = ()


class GestureInterpreter:
    """Convierte la secuencia de gestos estables en acciones del mouse."""

    def __init__(self, clock, hold_seconds=HOLD_SECONDS, scroll_step=SCROLL_STEP):
        self._clock = clock
        self._hold_seconds = hold_seconds
        self._scroll_step = scroll_step
        self._gesture = Gesture.NONE  # gesto del cuadro anterior
        self._pinch_started = None  # momento en que empezó el pellizco
        self._dragging = False  # el botón izquierdo está presionado
        self._scroll_reference = None  # altura de la mano desde la que se cuenta

    def update(self, gesture, hand_y=None):
        """Recibe el gesto estable y la altura de la mano en la cámara, en píxeles."""
        now = self._clock()
        actions = []
        if gesture is not self._gesture:
            # Primero se cierra el gesto anterior y después se abre el nuevo.
            actions += self._leave(self._gesture)
            actions += self._enter(gesture, now, hand_y)
            self._gesture = gesture
        actions += self._hold(gesture, now, hand_y)
        return Decision(move_cursor=self._moves_cursor(gesture), actions=tuple(actions))

    def finish(self):
        """Termina el gesto en curso al apagar los gestos o cerrar la aplicación.

        Si había un arrastre, devuelve la acción para soltar el botón, de modo que
        nunca quede presionado. Un pellizco a medias no genera click.
        """
        actions = [Action.LEFT_UP] if self._dragging else []
        self._gesture = Gesture.NONE
        self._pinch_started = None
        self._dragging = False
        self._scroll_reference = None
        return tuple(actions)

    def _leave(self, gesture):
        if gesture is Gesture.PINCH:
            # Se separaron los dedos: si ya era arrastre, se suelta; si no, es click.
            # También pasa si la mano sale de la cámara: nunca queda el botón apretado.
            action = Action.LEFT_UP if self._dragging else Action.LEFT_CLICK
            self._pinch_started = None
            self._dragging = False
            return [action]
        if gesture is Gesture.TWO_FINGERS:
            self._scroll_reference = None
        return []

    def _enter(self, gesture, now, hand_y):
        if gesture is Gesture.PINCH:
            # Todavía no se sabe si será click o arrastre: se mide cuánto dura.
            self._pinch_started = now
        elif gesture is Gesture.INDEX_DOWN:
            # El click derecho ocurre una sola vez, al entrar al gesto. Para repetirlo
            # hay que volver a subir el índice (PB-10 y PB-13).
            return [Action.RIGHT_CLICK]
        elif gesture is Gesture.TWO_FINGERS:
            self._scroll_reference = hand_y
        return []

    def _hold(self, gesture, now, hand_y):
        if gesture is Gesture.PINCH and not self._dragging:
            if now - self._pinch_started >= self._hold_seconds:
                # El pellizco duró lo suficiente: empieza el arrastre (PB-11).
                self._dragging = True
                return [Action.LEFT_DOWN]
        elif gesture is Gesture.TWO_FINGERS and hand_y is not None:
            return self._scroll(hand_y)
        return []

    def _scroll(self, hand_y):
        if self._scroll_reference is None:
            self._scroll_reference = hand_y
            return []
        # En la imagen, y crece hacia abajo: subir la mano da una diferencia positiva.
        steps = int((self._scroll_reference - hand_y) / self._scroll_step)
        if steps == 0:
            # La mano no se ha movido lo suficiente: no hay scroll (PB-12).
            return []
        # La referencia avanza solo los pasos usados, para no perder el resto.
        self._scroll_reference -= steps * self._scroll_step
        action = Action.SCROLL_UP if steps > 0 else Action.SCROLL_DOWN
        return [action] * abs(steps)

    def _moves_cursor(self, gesture):
        # El cursor sigue a la mano con la "L" y durante el arrastre. En el resto de los
        # gestos se congela, para que el click caiga donde se apuntaba.
        if gesture is Gesture.POINT:
            return True
        return gesture is Gesture.PINCH and self._dragging
