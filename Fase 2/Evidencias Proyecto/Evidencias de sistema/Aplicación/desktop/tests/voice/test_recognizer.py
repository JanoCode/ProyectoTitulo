"""Pruebas de la ubicación y la carga del modelo de voz."""

import pytest

from ergosense.voice import recognizer


def test_el_modelo_se_guarda_fuera_del_repositorio(monkeypatch, tmp_path):
    monkeypatch.delenv("ERGOSENSE_VOICE_MODEL", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    path = recognizer.model_path()
    assert path == tmp_path / "ErgoSense" / "models" / recognizer.MODEL_NAME


def test_una_variable_permite_usar_otra_carpeta(monkeypatch, tmp_path):
    monkeypatch.setenv("ERGOSENSE_VOICE_MODEL", str(tmp_path))
    assert recognizer.model_path() == tmp_path


def test_sin_modelo_se_informa_en_vez_de_fallar(monkeypatch, tmp_path):
    monkeypatch.setenv("ERGOSENSE_VOICE_MODEL", str(tmp_path / "no-existe"))
    monkeypatch.setattr(recognizer, "_model", None)
    with pytest.raises(recognizer.VoiceModelMissing):
        recognizer.load_model()


def test_una_ruta_sin_tildes_no_se_modifica():
    assert recognizer._ascii_path("C:/modelos/es") == "C:/modelos/es"


def test_una_ruta_con_tildes_se_convierte_a_la_ruta_corta(tmp_path):
    folder = tmp_path / "Aplicación"
    folder.mkdir()
    converted = recognizer._ascii_path(folder)
    # Si el disco no guarda nombres cortos, Windows devuelve la misma ruta.
    assert converted.isascii() or converted == str(folder)
