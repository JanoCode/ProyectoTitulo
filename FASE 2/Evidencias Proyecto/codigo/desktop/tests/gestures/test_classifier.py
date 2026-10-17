"""Pruebas del clasificador de gestos (Sprint 03: PB-08 y PB-13)."""

import pytest

from ergosense.gestures.classifier import Gesture, GestureClassifier, measure

# Mano inventada, en metros, con la muñeca en el origen y los dedos hacia arriba (+y).
BASES = {
    "index": (-0.025, 0.085, 0.0),
    "middle": (0.0, 0.09, 0.0),
    "ring": (0.02, 0.085, 0.0),
    "pinky": (0.04, 0.075, 0.0),
}
THUMB_TIPS = {
    "open": (-0.075, 0.065, 0.0),  # abierto hacia el costado: thumb_open 0,60
    "half": (-0.015, 0.06, 0.03),  # a medio camino: thumb_open 0,45
    "in": (-0.01, 0.075, 0.025),  # hacia adentro, sobre la palma: thumb_open 0,34
}


def finger(base, shape):
    """Los 4 puntos de un dedo: extendido, a medias o doblado hacia la palma."""
    x, y, z = base
    if shape == "extended":
        return [base, (x, y + 0.035, z), (x, y + 0.06, z), (x, y + 0.08, z)]
    if shape == "half":
        return [
            base,
            (x, y + 0.03, z + 0.005),
            (x, y + 0.035, z + 0.02),
            (x, y + 0.025, z + 0.035),
        ]
    return [base, (x, y + 0.025, z + 0.01), (x, y + 0.02, z + 0.03), (x, y, z + 0.03)]


def make_hand(
    thumb="open",
    index="extended",
    middle="folded",
    ring="folded",
    pinky="folded",
    scale=1.0,
):
    """Arma los 21 puntos en el orden de MediaPipe. Por defecto, la "L"."""
    tip = THUMB_TIPS[thumb]
    thumb_base = (-0.035, 0.04, 0.0)
    joint = tuple((a + b) / 2 for a, b in zip(thumb_base, tip, strict=True))
    points = [(0.0, 0.0, 0.0), (-0.02, 0.02, 0.0), thumb_base, joint, tip]
    for name, shape in [
        ("index", index),
        ("middle", middle),
        ("ring", ring),
        ("pinky", pinky),
    ]:
        points += finger(BASES[name], shape)
    return [tuple(c * scale for c in point) for point in points]


def classify(hand):
    return GestureClassifier().classify(hand)


def test_cp_03_04_la_l_es_mover_el_cursor():
    assert classify(make_hand()) is Gesture.POINT


def test_cp_03_04_pulgar_adentro_es_click_izquierdo():
    assert classify(make_hand(thumb="in")) is Gesture.THUMB_IN


def test_cp_03_04_bajar_el_indice_es_click_derecho():
    assert classify(make_hand(index="folded")) is Gesture.INDEX_DOWN


def test_cp_03_04_dos_dedos_es_scroll():
    hand = make_hand(thumb="in", middle="extended")
    assert classify(hand) is Gesture.TWO_FINGERS


def test_puno_queda_reservado_para_macros():
    # Índice abajo y pulgar adentro: los dos "botones" a la vez forman el puño.
    hand = make_hand(thumb="in", index="folded")
    assert classify(hand) is Gesture.FIST


def test_mano_abierta_queda_reservada_para_macros():
    hand = make_hand(middle="extended", ring="extended", pinky="extended")
    assert classify(hand) is Gesture.OPEN_HAND


def test_cp_03_10_pose_no_definida_no_es_gesto():
    # Índice y meñique extendidos: no corresponde a ningún gesto.
    hand = make_hand(thumb="in", pinky="extended")
    assert classify(hand) is Gesture.NONE


def test_cp_03_10_tres_dedos_no_es_gesto():
    hand = make_hand(thumb="in", middle="extended", ring="extended")
    assert classify(hand) is Gesture.NONE


def test_cp_03_10_el_pulgar_a_medio_camino_no_es_gesto():
    # Mientras el pulgar se mueve hacia adentro, ni mueve el cursor ni hace click.
    assert classify(make_hand(thumb="half")) is Gesture.NONE


def test_cp_03_10_el_indice_a_medio_camino_no_es_gesto():
    # Mientras el índice baja, todavía no es click derecho.
    assert classify(make_hand(index="half")) is Gesture.NONE


def test_sin_mano_no_hay_gesto():
    assert GestureClassifier().classify(None) is Gesture.NONE


def test_el_tamano_de_la_mano_no_cambia_el_gesto():
    # Una mano el doble de grande (o el doble de cerca) es el mismo gesto.
    assert classify(make_hand(scale=2.0)) is Gesture.POINT


def test_las_medidas_son_proporciones():
    small = measure(make_hand())
    big = measure(make_hand(scale=2.0))
    assert small.thumb_open == pytest.approx(big.thumb_open)
    assert small.index == pytest.approx(big.index)


def test_histeresis_el_click_izquierdo_no_se_corta_por_un_salto():
    # Pulgar a 0,45: entre entrar (0,4) y salir (0,5) del click izquierdo.
    border = make_hand(thumb="half")
    classifier = GestureClassifier()
    classifier.classify(make_hand(thumb="in"))
    assert classifier.classify(border) is Gesture.THUMB_IN  # con click, sigue


def test_histeresis_el_arrastre_no_se_corta_si_el_indice_se_relaja():
    # Durante el click izquierdo, el índice a medias no corta el arrastre.
    relaxed = make_hand(thumb="in", index="half")
    assert classify(relaxed) is Gesture.NONE  # sin click previo, no es gesto
    classifier = GestureClassifier()
    classifier.classify(make_hand(thumb="in"))
    assert classifier.classify(relaxed) is Gesture.THUMB_IN


def test_histeresis_el_click_derecho_no_se_corta_por_un_salto():
    # Índice a medias: entre entrar (1,2) y salir (1,4) del click derecho.
    border = make_hand(index="half")
    classifier = GestureClassifier()
    classifier.classify(make_hand(index="folded"))
    assert classifier.classify(border) is Gesture.INDEX_DOWN  # con click, sigue
