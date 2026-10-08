"""Punto de entrada de ErgoSense: crea los objetos y los conecta (Sprint 01)."""

import os
import sys
import time

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QStyle, QSystemTrayIcon

from ergosense.app.controller import MonitorController
from ergosense.monitoring.activity_period import ActivityPeriod
from ergosense.monitoring.activity_recorder import ActivityRecorder
from ergosense.monitoring.input_listener import InputListener
from ergosense.ui.main_window import MainWindow


def main():
    """Inicia la aplicación y devuelve su código de salida al cerrar la ventana."""
    app = QApplication(sys.argv)

    # Solo para pruebas de desarrollo: el usuario no puede cambiar los 60 minutos.
    # Las variables de entorno siempre son texto, por eso el valor por defecto va con str.
    limit = int(os.environ.get("ERGOSENSE_LIMIT_SECONDS", str(60 * 60)))

    # time.monotonic no salta si se cambia la hora del computador.
    period = ActivityPeriod(time.monotonic, limit_seconds=limit)
    recorder = ActivityRecorder(time.monotonic)

    # Ícono de la bandeja: sin él, Windows no muestra las notificaciones.
    icon = app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
    tray = QSystemTrayIcon(icon)
    tray.setToolTip("ErgoSense")
    tray.show()

    window = MainWindow(tray)
    controller = MonitorController(period, recorder, window)

    # El listener corre en sus propios hilos y solo anota la actividad.
    listener = InputListener(on_activity=recorder.register)
    listener.start()

    # El timer corre en el hilo principal: es el único que actualiza la ventana.
    timer = QTimer()
    timer.timeout.connect(controller.tick)
    timer.start(1000)  # Actualiza cada 1000 ms

    controller.start()
    window.show()

    exit_code = app.exec()  # el programa espera aquí hasta que cierres la ventana
    listener.stop()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
