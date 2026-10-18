"""Representación de una mano detectada, independiente de MediaPipe (PB-07)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Hand:
    """Los 21 puntos de una mano, en dos sistemas de coordenadas.

    image_points: (x, y) en píxeles de la imagen. Sirven para mover el cursor.
    world_points: (x, y, z) en metros, en 3D. Sirven para reconocer los gestos,
    porque sus distancias no cambian al girar la mano ni al alejarla de la cámara.
    """

    image_points: list[tuple[float, float]]
    world_points: list[tuple[float, float, float]]
