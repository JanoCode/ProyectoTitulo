"""Convierte segundos al formato HH:MM:SS, o '--:--:--' si no hay dato."""


def format_duration(seconds):
    """Devuelve un string con el formato HH:MM:SS para la cantidad de segundos dada."""
    if seconds is None:
        return "--:--:--"
    horas, resto = divmod(seconds, 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"
