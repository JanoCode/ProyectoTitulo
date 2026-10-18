"""Pruebas del movimiento del cursor (Sprint 03: PB-09)."""

from ergosense.gestures.cursor import CursorMapper

FRAME = (640, 480)  # ancho y alto de la imagen de la cámara
SCREEN = (0, 0, 1920, 1080)  # izquierda, arriba, ancho y alto de la pantalla
CENTER = (320, 240)  # centro de la imagen
RIGHT = (512, 240)  # borde derecho de la zona activa (80 % del ancho)


def make_mapper(screen=SCREEN, smoothing=1.0, dead_zone=0):
    # smoothing=1.0 y dead_zone=0 desactivan el suavizado para probar solo la zona activa.
    return CursorMapper(screen, smoothing=smoothing, dead_zone=dead_zone)


def test_cp_03_05_el_centro_de_la_camara_es_el_centro_de_la_pantalla():
    assert make_mapper().update(CENTER, FRAME) == (960, 540)


def test_la_zona_activa_cubre_toda_la_pantalla():
    mapper = make_mapper()
    assert mapper.update((128, 96), FRAME) == (0, 0)  # 20 % del ancho y del alto
    assert mapper.update((512, 384), FRAME) == (1919, 1079)  # 80 %: último píxel


def test_fuera_de_la_zona_activa_el_cursor_queda_en_el_borde():
    assert make_mapper().update((10, 10), FRAME) == (0, 0)


def test_respeta_la_posicion_de_la_pantalla():
    # Un monitor vertical a la izquierda del principal tiene coordenadas negativas.
    mapper = make_mapper(screen=(-768, -99, 768, 1366))
    assert mapper.update(CENTER, FRAME) == (-384, 584)


def test_cp_03_05_el_suavizado_evita_saltos_bruscos():
    mapper = make_mapper(smoothing=0.5)
    mapper.update(CENTER, FRAME)
    # El destino es el borde derecho (1920), pero solo avanza la mitad del camino.
    assert mapper.update(RIGHT, FRAME) == (1440, 540)


def test_la_zona_muerta_ignora_los_temblores_de_la_mano():
    mapper = make_mapper(dead_zone=5)
    mapper.update(CENTER, FRAME)
    # Medio píxel en la cámara son unos 3 píxeles en la pantalla: no se mueve.
    assert mapper.update((320.5, 240.5), FRAME) == (960, 540)


def test_reset_hace_que_vaya_directo_a_la_mano():
    mapper = make_mapper(smoothing=0.5)
    mapper.update(CENTER, FRAME)
    mapper.reset()  # la mano salió de la imagen
    assert mapper.update(RIGHT, FRAME) == (1919, 540)
