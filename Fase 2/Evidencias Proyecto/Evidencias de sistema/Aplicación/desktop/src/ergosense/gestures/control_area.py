SCREEN_ASPECT = 16 / 9
AREA_WIDTH = 0.36
CURSOR_INSET = 0.18


def control_area(side, frame_size=(16, 9)):
    if side not in ("left", "right"):
        raise ValueError("El lado debe ser left o right")
    width, height = frame_size
    if width <= 0 or height <= 0:
        raise ValueError("El video debe tener dimensiones positivas")
    area_width = min(AREA_WIDTH, 0.8 * height * SCREEN_ASPECT / width)
    area_height = area_width * width / (SCREEN_ASPECT * height)
    left = 0.94 - area_width if side == "right" else 0.06
    top = (1 - area_height) / 2
    return left, top, left + area_width, top + area_height


def contains(point, frame_size, bounds):
    x, y = point
    width, height = frame_size
    left, top, right, bottom = bounds
    return left <= x / width <= right and top <= y / height <= bottom


def cursor_area(bounds):
    left, top, right, bottom = bounds
    dx, dy = (right - left) * CURSOR_INSET, (bottom - top) * CURSOR_INSET
    return left + dx, top + dy, right - dx, bottom - dy
