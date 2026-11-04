"""Pruebas de la ubicación, la descarga y la carga del modelo de voz."""

import hashlib
import io
import urllib.error
import zipfile

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


# --- Descarga automática, con un servidor falso (las pruebas no usan internet)


class FakeResponse(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.headers = {"Content-Length": str(len(data))}


def model_zip(with_model=True):
    """Un .zip pequeño con la misma estructura que el del modelo real."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zipped:
        name = "am/final.mdl" if with_model else "LEEME.txt"
        zipped.writestr(f"{recognizer.MODEL_NAME}/{name}", b"modelo")
    return buffer.getvalue()


@pytest.fixture
def server(monkeypatch, tmp_path):
    """Sirve el .zip indicado y anota cuántas veces se descargó."""
    monkeypatch.setenv("ERGOSENSE_VOICE_MODEL", str(tmp_path / "models" / "es"))
    state = {"data": model_zip(), "downloads": 0}

    def urlopen(url, timeout):
        assert url == recognizer.MODEL_URL
        state["downloads"] += 1
        return FakeResponse(state["data"])

    def serve(data):
        state["data"] = data
        monkeypatch.setattr(
            recognizer, "MODEL_SHA256", hashlib.sha256(data).hexdigest()
        )

    monkeypatch.setattr(recognizer.urllib.request, "urlopen", urlopen)
    serve(state["data"])
    state["serve"] = serve
    return state


def test_descarga_e_instala_el_modelo_e_informa_el_avance(server):
    progress = []
    target = recognizer.download_model(progress=progress.append)
    assert recognizer.is_installed(target)
    assert progress[-1] == 100
    # No quedan carpetas temporales junto al modelo.
    assert [path.name for path in target.parent.iterdir()] == ["es"]


def test_si_ya_esta_instalado_no_se_descarga_otra_vez(server):
    recognizer.download_model()
    recognizer.download_model()
    assert server["downloads"] == 1


def test_un_archivo_alterado_no_se_instala(server, monkeypatch):
    monkeypatch.setattr(recognizer, "MODEL_SHA256", "0" * 64)
    with pytest.raises(recognizer.ModelDownloadError):
        recognizer.download_model()
    assert not recognizer.is_installed()


def test_un_archivo_sin_el_modelo_no_se_instala(server):
    server["serve"](model_zip(with_model=False))
    with pytest.raises(recognizer.ModelDownloadError):
        recognizer.download_model()
    assert not recognizer.is_installed()


def test_sin_internet_se_informa_un_error_de_descarga(server, monkeypatch):
    def offline(url, timeout):
        raise urllib.error.URLError("sin conexión")

    monkeypatch.setattr(recognizer.urllib.request, "urlopen", offline)
    with pytest.raises(recognizer.ModelDownloadError):
        recognizer.download_model()


def test_al_cancelar_no_queda_nada_a_medias(server):
    with pytest.raises(recognizer.DownloadCancelled):
        recognizer.download_model(cancelled=lambda: True)
    folder = recognizer.model_path().parent
    assert not recognizer.is_installed()
    assert list(folder.iterdir()) == []


def test_se_borran_los_restos_de_una_descarga_cortada(server):
    leftover = recognizer.model_path().parent / f"{recognizer.DOWNLOAD_PREFIX}vieja"
    leftover.mkdir(parents=True)
    recognizer.download_model()
    assert not leftover.exists()
