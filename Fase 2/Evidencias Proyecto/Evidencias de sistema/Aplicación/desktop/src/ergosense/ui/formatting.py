"""Formato de tiempos para mostrarlos en la interfaz."""


def format_duration(seconds):
    """Devuelve un string con el formato HH:MM:SS para la cantidad de segundos dada."""
    if seconds is None:
        return "--:--:--"
    horas, resto = divmod(seconds, 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"


def format_elapsed(seconds):
    """Describe hace cuánto pasó algo, por ejemplo "hace 12 segundos"."""
    if seconds is None:
        return "Sin actividad aún"
    if seconds < 1:
        return "ahora"
    if seconds < 60:
        return "hace 1 segundo" if seconds == 1 else f"hace {seconds} segundos"
    minutes = seconds // 60
    if minutes < 60:
        return "hace 1 minuto" if minutes == 1 else f"hace {minutes} minutos"
    hours, minutes = divmod(minutes, 60)
    return f"hace {hours} h {minutes} min"
