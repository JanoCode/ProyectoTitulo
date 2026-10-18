"""Cadena completa del control por gestos, cuadro a cuadro (PB-07 a PB-13).

Une las piezas de los pasos anteriores: mano -> gesto del cuadro -> gesto estable
-> decisión -> posición del cursor. No toca la cámara ni el mouse, por lo que se
prueba sin hardware.
"""

from dataclasses import dataclass

from ergosense.actions.action import Action
from ergosense.gestures.classifier import Gesture, GestureClassifier
from ergosense.gestures.cursor import CURSOR_POINT, CursorMapper
from ergosense.gestures.interpreter import GestureInterpreter, GestureStabilizer


@dataclass(frozen=True)
class Step:
    """Resultado de un cuadro: el gesto, a dónde mover el cursor y qué acciones hacer."""

    gesture: Gesture
    cursor: tuple[int, int] | None = None  # None: el cursor no se mueve
    actions: tuple[Action, ...] = ()


class GesturePipeline:
    """Convierte cada mano detectada en movimiento del cursor y acciones del mouse."""

    def __init__(self, screen, clock, classifier=None):
        # El clasificador se puede reemplazar en las pruebas por uno falso.
        self._classifier = classifier or GestureClassifier()
        self._stabilizer = GestureStabilizer()
        self._interpreter = GestureInterpreter(clock)
        self._mapper = CursorMapper(screen)

    def process(self, hand, frame_size):
        """Procesa la mano de un cuadro (o None si no hay) y devuelve un Step."""
        raw = self._classifier.classify(None if hand is None else hand.world_points)
        gesture = self._stabilizer.update(raw)
        # El centro de la palma da la posición del cursor y la altura para el scroll.
        palm = None if hand is None else hand.image_points[CURSOR_POINT]
        decision = self._interpreter.update(gesture, None if palm is None else palm[1])

        cursor = None
        if hand is None:
            # Al volver la mano, el cursor irá directo a ella.
            self._mapper.reset()
        elif decision.move_cursor:
            cursor = self._mapper.update(palm, frame_size)
        return Step(gesture=gesture, cursor=cursor, actions=decision.actions)

    def finish(self):
        """Acciones para terminar limpio, por ejemplo soltar el botón de un arrastre."""
        return self._interpreter.finish()
