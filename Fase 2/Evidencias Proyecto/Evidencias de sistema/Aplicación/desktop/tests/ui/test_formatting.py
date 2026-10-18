"""Pruebas del formato de tiempo de la interfaz."""

from ergosense.ui.formatting import format_duration


def test_cero_segundos():
    assert format_duration(0) == "00:00:00"


def test_minutos_y_segundos():
    assert format_duration(125) == "00:02:05"


def test_incluye_las_horas():
    assert format_duration(1 * 3600 + 35 * 60 + 7) == "01:35:07"


# Esta ultima prueba es para el caso en que no hay dato, por ejemplo cuando se inicia la aplicacion y aun no se ha registrado actividad. En ese caso se muestra "--:--:--" en la interfaz.
def test_sin_dato_muestra_guiones():
    assert format_duration(None) == "--:--:--"
