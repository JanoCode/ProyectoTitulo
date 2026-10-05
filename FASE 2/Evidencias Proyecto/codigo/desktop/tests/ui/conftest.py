"""Configuración compartida de las pruebas de la interfaz."""

import os

import pytest
from PySide6.QtWidgets import QApplication

# Las pruebas no abren ventanas en la pantalla.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    """Entrega la única QApplication del programa, creándola si aún no existe."""
    return QApplication.instance() or QApplication([])
