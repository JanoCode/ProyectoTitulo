"""Pruebas del formato de tiempo de la interfaz."""

from ergosense.ui.formatting import format_duration, format_elapsed


def test_cero_segundos():
    assert format_duration(0) == "00:00:00"


def test_minutos_y_segundos():
    assert format_duration(125) == "00:02:05"


def test_incluye_las_horas():
    assert format_duration(1 * 3600 + 35 * 60 + 7) == "01:35:07"


# Esta ultima prueba es para el caso en que no hay dato, por ejemplo cuando se inicia la aplicacion y aun no se ha registrado actividad. En ese caso se muestra "--:--:--" en la interfaz.
def test_sin_dato_muestra_guiones():
    assert format_duration(None) == "--:--:--"


def test_ultima_actividad_en_segundos():
    assert format_elapsed(0) == "ahora"
    assert format_elapsed(1) == "hace 1 segundo"
    assert format_elapsed(12) == "hace 12 segundos"


def test_ultima_actividad_en_minutos_y_horas():
    assert format_elapsed(60) == "hace 1 minuto"
    assert format_elapsed(125) == "hace 2 minutos"
    assert format_elapsed(3 * 3600 + 5 * 60) == "hace 3 h 5 min"


def test_sin_actividad_lo_dice_en_palabras():
    assert format_elapsed(None) == "Sin actividad aún"
