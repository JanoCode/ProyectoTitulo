"""Punto de entrada de ErgoSense: crea los objetos y los conecta (Sprint 01)."""

import os
import sys
import time
from datetime import UTC, datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QMessageBox,
    QStyle,
    QSystemTrayIcon,
)

from ergosense.api_client import ApiClient, ApiClientError
from ergosense.app.controller import MonitorController
from ergosense.app.remote_session import RemoteUsageSession
from ergosense.monitoring.activity_period import ActivityPeriod
from ergosense.monitoring.activity_recorder import ActivityRecorder
from ergosense.monitoring.inactivity import InactivityMonitor
from ergosense.monitoring.input_listener import InputListener
from ergosense.ui.auth_dialogs import LoginDialog
from ergosense.ui.main_window import MainWindow


def main():
    """Inicia la aplicación y devuelve su código de salida al cerrar la ventana."""
    app = QApplication(sys.argv)

    # La URL puede cambiar en otro computador sin modificar el código.
    api_url = os.environ.get("ERGOSENSE_API_URL", "http://127.0.0.1:8000/api/v1")
    api_client = ApiClient(api_url)

    # El refresh token protegido permite reabrir la aplicación sin guardar la clave.
    if not api_client.restore_session():
        login_dialog = LoginDialog(api_client)
        if login_dialog.exec() != QDialog.DialogCode.Accepted:
            api_client.close()
            return 0

    # Solo para pruebas de desarrollo: el usuario no puede cambiar los 60 minutos.
    # Las variables de entorno siempre son texto, por eso el valor por defecto va con str.
    limit = int(os.environ.get("ERGOSENSE_LIMIT_SECONDS", str(60 * 60)))

    # time.monotonic no salta si se cambia la hora del computador.
    period = ActivityPeriod(time.monotonic, limit_seconds=limit)
    recorder = ActivityRecorder(time.monotonic)

    # El producto usa la configuración del servidor. La variable opcional solo
    # permite demostrar una pausa sin esperar diez minutos.
    settings = api_client.settings or api_client.get_settings()
    inactivity_seconds = int(
        os.environ.get(
            "ERGOSENSE_INACTIVITY_SECONDS",
            str(settings["inactivity_break_minutes"] * 60),
        )
    )
    inactivity = InactivityMonitor(
        time.monotonic,
        lambda: datetime.now(UTC),
        inactivity_seconds,
    )

    # Ícono de la bandeja: sin él, Windows no muestra las notificaciones.
    icon = app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
    tray = QSystemTrayIcon(icon)
    tray.setToolTip("ErgoSense")
    tray.show()

    window = MainWindow(tray)
    window.show_user(api_client.user["name"], api_client.user["email"])

    remote_session = RemoteUsageSession(api_client)
    try:
        remote_session.start()
    except ApiClientError as error:
        QMessageBox.critical(None, "ErgoSense", str(error))
        api_client.close()
        return 1

    controller = MonitorController(
        period,
        recorder,
        window,
        inactivity_monitor=inactivity,
        remote_session=remote_session,
    )

    # El listener corre en sus propios hilos y solo anota la actividad.
    def register_activity():
        # Los dos objetos son seguros entre hilos y solo guardan tiempos.
        recorder.register()
        inactivity.register_activity()

    listener = InputListener(on_activity=register_activity)
    listener.start()

    # El timer corre en el hilo principal: es el único que actualiza la ventana.
    timer = QTimer()
    timer.timeout.connect(controller.tick)
    timer.start(1000)  # Actualiza cada 1000 ms

    controller.start()
    window.show()

    closed = False

    def close_resources(logout=False):
        """Cierra una sola vez listeners, pausa, sesión, tokens y conexiones."""
        nonlocal closed
        if closed:
            return
        closed = True
        listener.stop()
        try:
            controller.finish()
            if logout:
                api_client.logout()
        except ApiClientError as error:
            # Durante el cierre no se deja una excepción técnica en pantalla.
            if logout:
                QMessageBox.warning(window, "ErgoSense", str(error))
        finally:
            api_client.close()

    def logout():
        close_resources(logout=True)
        app.quit()

    window.logout_requested.connect(logout)
    app.aboutToQuit.connect(close_resources)

    exit_code = app.exec()  # el programa espera aquí hasta que cierres la ventana
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
