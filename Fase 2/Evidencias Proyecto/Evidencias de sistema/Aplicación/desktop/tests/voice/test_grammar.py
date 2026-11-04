"""Pruebas de la lista de frases que reconoce Vosk (PB-16 y RNF-03)."""

import json

from ergosense.voice.commands import COMMANDS
from ergosense.voice.grammar import UNKNOWN, grammar_json, phrases


def test_incluye_todos_los_comandos_completos():
    for phrase in COMMANDS:
        assert phrase in phrases()


def test_incluye_palabras_de_relleno_y_la_palabra_desconocida():
    assert "trabajar" in phrases()  # se parece a "bajar"
    assert "subiendo" in phrases()  # se parece a "subir"
    assert phrases()[-1] == UNKNOWN


def test_ninguna_palabra_de_relleno_es_una_palabra_de_comando():
    # Si "voz" fuera relleno, Vosk podría elegir "voz" sola en vez de "activar voz".
    command_words = {word for phrase in COMMANDS for word in phrase.split()}
    filler = set(phrases()) - set(COMMANDS) - {UNKNOWN}
    assert not filler & command_words


def test_el_formato_para_vosk_es_una_lista_json_con_tildes():
    assert json.loads(grammar_json()) == phrases()
    assert "días" in grammar_json()
