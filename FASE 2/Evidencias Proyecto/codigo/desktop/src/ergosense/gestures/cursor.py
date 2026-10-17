"""Conversión de la posición de la mano en la posición del cursor (PB-09).

Usa solo la parte central de la imagen de la cámara (zona activa) y la estira
hasta cubrir la pantalla, suavizando el movimiento e ignorando los temblores.
No mueve el mouse: solo calcula hacia dónde debe ir.
"""

import math

# Ajustes de sensibilidad (SB03-T10).
ACTIVE_MARGIN = 0.2  # se ignora el 20 % de cada borde de la imagen
SMOOTHING = 0.35  # fracción del camino que avanza el cursor en cada cuadro
DEAD_ZONE = 3  # píxeles: movimientos menores se ignoran


def _clamp(value, low, high):
    return min(max(value, low), high)


class CursorMapper:
    """Calcula la posición del cursor en la pantalla a partir de un punto de la imagen."""

    def __init__(
        self,
        screen,
        smoothing=SMOOTHING,
        dead_zone=DEAD_ZONE,
        margin=ACTIVE_MARGIN,
    ):
        # screen: (izquierda, arriba, ancho, alto). Un monitor a la izquierda del
        # principal tiene coordenadas negativas, por eso se guarda su origen.
        self._left, self._top, self._width, self._height = screen
        self._smoothing = smoothing
        self._dead_zone = dead_zone
        self._margin = margin
        # Posición suavizada, con decimales. None mientras no haya cursor.
        self._position = None

    def update(self, point, frame_size):
        """Devuelve la posición (x, y) del cursor en píxeles de la pantalla."""
        target = self._to_screen(point, frame_size)

        if self._position is None:
            # Primera vez, o después de reset(): va directo a la mano.
            self._position = target
        elif math.dist(target, self._position) >= self._dead_zone:
            # Avanza solo una parte del camino: así no hay saltos bruscos. esto es cuando lo identifica por primera vez para que el cursos vaya directo
            x, y = self._position
            target_x, target_y = target
            self._position = (
                x + self._smoothing * (target_x - x),
                y + self._smoothing * (target_y - y),
            )
        # Si el destino está dentro de la zona muerta, el cursor no se mueve.

        return self._to_pixel(self._position)

    def reset(self):
        """Olvida la posición: al volver la mano, el cursor irá directo a ella."""
        self._position = None

    def _to_screen(self, point, frame_size):
        x, y = point
        frame_width, frame_height = frame_size
        # Fracción dentro de la zona activa: 0 en su borde izquierdo o superior y 1
        # en el derecho o inferior. Fuera de la zona se queda en 0 o en 1.
        active = 1 - 2 * self._margin

        #Para que el cursos no se salga de la pantalla si nosotros sacamops la mano
        fraction_x = _clamp((x / frame_width - self._margin) / active, 0, 1) 
        fraction_y = _clamp((y / frame_height - self._margin) / active, 0, 1)
        return (
            self._left + fraction_x * self._width,
            self._top + fraction_y * self._height,
        )

    def _to_pixel(self, position):
        # El último píxel de una pantalla de 1920 es el 1919, porque se cuenta desde 0.
        x, y = position
        pixel_x = _clamp(math.floor(x), self._left, self._left + self._width - 1)
        pixel_y = _clamp(math.floor(y), self._top, self._top + self._height - 1)
        return (pixel_x, pixel_y)
