AREAS = {
    "right": (0.58, 0.18, 0.94, 0.82),
    "left": (0.06, 0.18, 0.42, 0.82),
}


def control_area(side):
    if side not in AREAS:
        raise ValueError("El lado debe ser left o right")
    return AREAS[side]


def contains(point, frame_size, bounds):
    x, y = point
    width, height = frame_size
    left, top, right, bottom = bounds
    return left <= x / width <= right and top <= y / height <= bottom
