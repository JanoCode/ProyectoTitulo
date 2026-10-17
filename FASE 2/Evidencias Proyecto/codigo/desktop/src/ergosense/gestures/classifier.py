"""Clasificación de gestos de la mano mediante reglas geométricas (PB-08 y PB-13).

Recibe los 21 puntos de la mano en 3D y decide qué gesto es. No usa cámara ni
MediaPipe, por lo que se prueba con manos inventadas. No hace falta entrenar un
modelo: cada gesto se reconoce por qué dedos están extendidos o doblados y por
qué tan abierto está el pulgar. Los gestos se hacen con la palma de frente a la
cámara, partiendo de la "L" (índice arriba y pulgar abierto): el pulgar funciona
como el botón izquierdo y el índice como el derecho.
"""

import math
from dataclasses import dataclass
from enum import StrEnum

# Umbrales, calibrados con la mano real (SB03-T10 y SB03-T19).
EXTENDED_REACH = 1.5  # dedo extendido: su punta queda lejos de la muñeca
FOLDED_REACH = 1.2  # dedo doblado: su punta vuelve hacia la palma
INDEX_DOWN_EXIT = 1.4  # para salir del click derecho (histéresis)
THUMB_OPEN_MIN = 0.55  # pulgar abierto: lejos del nudillo del índice
THUMB_IN_ENTER = 0.4  # para entrar al click izquierdo: pulgar hacia adentro
THUMB_IN_EXIT = 0.5  # para salir del click izquierdo (histéresis)

# Puntos de MediaPipe que usan las reglas.
WRIST = 0
THUMB_TIP = 4
INDEX_BASE = 5
MIDDLE_BASE = 9
# Nudillo y punta de cada dedo.
FINGERS = {"index": (5, 8), "middle": (9, 12), "ring": (13, 16), "pinky": (17, 20)}


class Gesture(StrEnum):
    """Gestos reconocidos. Los valores son los nombres que usarán las macros."""

    NONE = "none"  # pose no definida: no hace nada (PB-13)
    POINT = "point"  # "L": índice arriba y pulgar abierto: mover el cursor
    THUMB_IN = "thumb_in"  # desde la "L", pulgar hacia adentro: click izquierdo
    INDEX_DOWN = "index_down"  # desde la "L", bajar el índice: click derecho
    TWO_FINGERS = "two_fingers"  # índice y medio arriba: scroll
    FIST = "fist"  # reservado para macros (Sprint 05)
    OPEN_HAND = "open_hand"  # reservado para macros (Sprint 05)


@dataclass(frozen=True)
class HandMeasures:
    """Medidas de la mano, todas como proporciones.

    index, middle, ring y pinky: cuánto se aleja la punta de cada dedo de la
    muñeca, comparado con su nudillo. Sobre 1,5 está extendido; bajo 1,2, doblado.
    thumb_open: distancia de la punta del pulgar al nudillo del índice, en
    proporción al tamaño de la mano. Grande con el pulgar abierto; chica con el
    pulgar hacia adentro.
    """

    index: float
    middle: float
    ring: float
    pinky: float
    thumb_open: float


def measure(points):
    """Calcula las medidas de la mano a partir de sus 21 puntos en 3D."""
    # Tamaño de la mano: de la muñeca a la base del dedo medio. Al dividir por él,
    # da lo mismo si la mano es grande o chica, o si está cerca o lejos.
    size = math.dist(points[WRIST], points[MIDDLE_BASE])

    def reach(base, tip):
        # Un dedo recto lleva su punta lejos de la muñeca; uno doblado la regresa.
        to_tip = math.dist(points[WRIST], points[tip])
        to_base = math.dist(points[WRIST], points[base])
        return to_tip / to_base

    return HandMeasures(
        index=reach(*FINGERS["index"]),
        middle=reach(*FINGERS["middle"]),
        ring=reach(*FINGERS["ring"]),
        pinky=reach(*FINGERS["pinky"]),
        thumb_open=math.dist(points[THUMB_TIP], points[INDEX_BASE]) / size,
    )


def _extended(reach):
    return reach > EXTENDED_REACH


def _folded(reach):
    return reach < FOLDED_REACH


class GestureClassifier:
    """Reconoce el gesto de cada cuadro, recordando el anterior para la histéresis."""

    def __init__(self):
        # Gesto del cuadro anterior: decide qué umbral usar para los clicks.
        self._previous = Gesture.NONE

    def classify(self, points):
        """Devuelve el gesto de la mano, o NONE si no hay mano."""
        gesture = Gesture.NONE if points is None else self._classify(measure(points))
        self._previous = gesture
        return gesture

    def _classify(self, m):
        # Las reglas van de la más general a la más específica; la primera que se
        # cumple decide el gesto.
        if all(_extended(r) for r in (m.index, m.middle, m.ring, m.pinky)):
            return Gesture.OPEN_HAND
        if (
            _extended(m.index)
            and _extended(m.middle)
            and _folded(m.ring)
            and _folded(m.pinky)
        ):
            return Gesture.TWO_FINGERS
        # Los gestos que quedan necesitan medio, anular y meñique doblados; cualquier
        # otra combinación de dedos no es un gesto definido (PB-13).
        if not all(_folded(r) for r in (m.middle, m.ring, m.pinky)):
            return Gesture.NONE

        # Histéresis: si ya se estaba haciendo un click, se exige menos para
        # mantenerlo que para empezarlo. Así un salto de los números no lo corta.
        clicking_left = self._previous is Gesture.THUMB_IN
        thumb_in_max = THUMB_IN_EXIT if clicking_left else THUMB_IN_ENTER
        index_down_max = (
            INDEX_DOWN_EXIT if self._previous is Gesture.INDEX_DOWN else FOLDED_REACH
        )
        # Durante el click izquierdo, o un arrastre, basta con que el índice no se
        # doble del todo: si se relaja un poco, el arrastre no se corta.
        index_up_min = FOLDED_REACH if clicking_left else EXTENDED_REACH
        thumb_in = m.thumb_open < thumb_in_max
        thumb_open = m.thumb_open > THUMB_OPEN_MIN

        if m.index < index_down_max:
            # Índice abajo: con el pulgar abierto es el click derecho; con el pulgar
            # adentro, la mano queda cerrada: el puño.
            if thumb_open:
                return Gesture.INDEX_DOWN
            if thumb_in:
                return Gesture.FIST
        elif m.index > index_up_min:
            # Índice arriba: con el pulgar abierto es la "L"; adentro, el click.
            if thumb_in:
                return Gesture.THUMB_IN
            if thumb_open:
                return Gesture.POINT
        # Índice o pulgar a medio camino, por ejemplo mientras se mueve un dedo:
        # en ese instante no se hace nada.
        return Gesture.NONE
