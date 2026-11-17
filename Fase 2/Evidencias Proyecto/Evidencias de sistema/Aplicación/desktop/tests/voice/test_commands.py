import pytest

from ergosense.actions.action import Action
from ergosense.voice.commands import COMMANDS, resolve_command


@pytest.mark.parametrize("phrase, action", COMMANDS.items())
def test_every_command_has_one_action(phrase, action):
    assert resolve_command(phrase) == action


@pytest.mark.parametrize(
    "phrase",
    [
        "",
        "ruido",
        "subir un poco",
        "no activar voz",
        "activar gesto",
        "clic",
        "bajar volumen",
    ],
)
def test_unknown_or_similar_phrases_are_rejected(phrase):
    assert resolve_command(phrase) is None


def test_normalizes_case_accents_and_whitespace():
    assert resolve_command("  CLÍC   IZQUIERDO ") is Action.LEFT_CLICK


def test_base_commands_are_read_only():
    with pytest.raises(TypeError):
        COMMANDS["subir"] = Action.LEFT_CLICK
