"""Clasificación de gestos de la mano mediante reglas geométricas (PB-08 y PB-13).

Recibe los 21 puntos de la mano en 3D y decide qué gesto es. No usa cámara ni
MediaPipe, por lo que se prueba con manos inventadas. No hace falta entrenar un
modelo: cada gesto se reconoce por qué dedos están extendidos o doblados y por
qué tan abierto está el pulgar. Los gestos se hacen con la palma de frente a la
cámara y partiendo de la mano abierta, que mueve el cursor: el pulgar funciona
como el botón izquierdo y el índice como el derecho.
"""

import math
from dataclasses import dataclass
from enum import StrEnum

# Umbrales, calibrados con la mano real con scripts/calibrate_gestures.py
# (SB03-T10 y SB03-T19). Medianas medidas: dedos estirados de 1,72 a 1,89; puño
# de 0,64 a 0,87; índice abajo con la mano abierta 1,36; pulgar abierto 1,14 y
# pulgar adentro 0,72.
EXTENDED_REACH = 1.6  # dedo extendido: su punta queda lejos de la muñeca
FOLDED_REACH = 1.35  # dedo doblado: su punta vuelve hacia la palma
# Con los otros dedos estirados, el índice no alcanza a doblarse del todo, por
# eso el click derecho tiene sus propios umbrales.
INDEX_DOWN_ENTER = 1.5  # para entrar al click derecho
INDEX_DOWN_EXIT = 1.58  # para salir del click derecho (histéresis)
THUMB_OPEN_MIN = 1.0  # pulgar abierto: lejos de la base del meñique
THUMB_IN_ENTER = 0.85  # para entrar al click izquierdo: pulgar hacia adentro
THUMB_IN_EXIT = 0.95  # para salir del click izquierdo (histéresis)

# Puntos de MediaPipe que usan las reglas.
WRIST = 0
THUMB_TIP = 4
MIDDLE_BASE = 9
PINKY_BASE = 17
# Nudillo y punta de cada dedo.
FINGERS = {"index": (5, 8), "middle": (9, 12), "ring": (13, 16), "pinky": (17, 20)}


class Gesture(StrEnum):
    """Gestos reconocidos. Los valores son los nombres que usarán las macros."""

    NONE = "none"  # pose no definida: no hace nada (PB-13)
    POINT = "point"  # mano abierta: mover el cursor
    THUMB_IN = "thumb_in"  # mano abierta con el pulgar adentro: click izquierdo
    INDEX_DOWN = "index_down"  # mano abierta con el índice abajo: click derecho
    TWO_FINGERS = "two_fingers"  # índice y medio arriba: scroll
    FIST = "fist"  # reservado para macros (Sprint 05)
    L_SHAPE = "l_shape"  # índice y pulgar en "L": reservado para macros (Sprint 05)


# Gestos que parten de la mano abierta: mientras se pasa de uno a otro, los dedos
# que no se mueven pueden relajarse un poco sin que el gesto se corte.
OPEN_HAND_GESTURES = {Gesture.POINT, Gesture.THUMB_IN, Gesture.INDEX_DOWN}


@dataclass(frozen=True)
class HandMeasures:
    """Medidas de la mano, todas como proporciones.

    index, middle, ring y pinky: cuánto se aleja la punta de cada dedo de la
    muñeca, comparado con su nudillo. Sobre 1,6 está extendido; bajo 1,35, doblado.
    thumb_open: distancia de la punta del pulgar a la base del meñique, en
    proporción al tamaño de la mano. Grande con el pulgar abierto; chica con el
    pulgar hacia adentro, porque al doblarlo cruza la palma hacia el meñique.
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
        thumb_open=math.dist(points[THUMB_TIP], points[PINKY_BASE]) / size,
    )


def _extended(reach):
    return reach > EXTENDED_REACH


def _folded(reach):
    return reach < FOLDED_REACH


class GestureClassifier:
    """Reconoce el gesto de cada cuadro, recordando el anterior para la histéresis."""

    def __init__(self):
        # Gesto del cuadro anterior: decide qué umbral usar en cada regla.
        self._previous = Gesture.NONE

    def classify(self, points):
        """Devuelve el gesto de la mano, o NONE si no hay mano."""
        gesture = Gesture.NONE if points is None else self._classify(measure(points))
        self._previous = gesture
        return gesture

    def _classify(self, m):
        others = (m.middle, m.ring, m.pinky)
        # Histéresis: si ya se estaba en un gesto de la mano abierta, basta con que
        # medio, anular y meñique no estén doblados; para llegar, deben estar
        # extendidos. Así, al doblar el índice, el medio puede acompañarlo un poco.
        others_min = (
            FOLDED_REACH if self._previous in OPEN_HAND_GESTURES else EXTENDED_REACH
        )

        if all(r > others_min for r in others):
            return self._classify_open_hand(m)
        if (
            _extended(m.index)
            and _extended(m.middle)
            and _folded(m.ring)
            and _folded(m.pinky)
        ):
            return Gesture.TWO_FINGERS
        if all(_folded(r) for r in others):
            # Mano cerrada: solo se reconocen los gestos reservados para macros.
            if _folded(m.index) and m.thumb_open < THUMB_IN_ENTER:
                return Gesture.FIST
            if _extended(m.index) and m.thumb_open > THUMB_OPEN_MIN:
                return Gesture.L_SHAPE
        # Cualquier otra combinación de dedos no es un gesto definido (PB-13).
        return Gesture.NONE

    def _classify_open_hand(self, m):
        # Histéresis de los clicks: si ya se estaba haciendo uno, se exige menos
        # para mantenerlo que para empezarlo. Así un salto de los números no lo corta.
        clicking_left = self._previous is Gesture.THUMB_IN
        thumb_in_max = THUMB_IN_EXIT if clicking_left else THUMB_IN_ENTER
        index_down_max = (
            INDEX_DOWN_EXIT
            if self._previous is Gesture.INDEX_DOWN
            else INDEX_DOWN_ENTER
        )
        # Durante el click izquierdo, o un arrastre, basta con que el índice no se
        # doble del todo: si se relaja un poco, el arrastre no se corta.
        index_up_min = FOLDED_REACH if clicking_left else EXTENDED_REACH

        thumb_in = m.thumb_open < thumb_in_max
        thumb_open = m.thumb_open > THUMB_OPEN_MIN
        index_up = m.index > index_up_min
        index_down = m.index < index_down_max

        # Cada dedo es un botón: el pulgar el izquierdo y el índice el derecho.
        if index_up and thumb_open:
            return Gesture.POINT
        if index_up and thumb_in:
            return Gesture.THUMB_IN
        if index_down and thumb_open:
            return Gesture.INDEX_DOWN
        # Los dos dedos abajo a la vez, o alguno a medio camino: no se hace nada.
        return Gesture.NONE
