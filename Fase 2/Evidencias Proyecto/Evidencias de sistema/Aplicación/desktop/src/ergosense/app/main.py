"""Punto de entrada de ErgoSense: crea los objetos y los conecta (Sprints 01 a 03)."""

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

from ergosense.actions.executor import ActionExecutor
from ergosense.actions.mouse import MouseActions
from ergosense.actions.screen import primary_screen
from ergosense.api_client import ApiClient, ApiClientError
from ergosense.app.controller import MonitorController
from ergosense.app.preferences import PreferencesController
from ergosense.app.remote_session import RemoteUsageSession
from ergosense.gestures.camera import Camera
from ergosense.gestures.hand_tracker import HandTracker
from ergosense.gestures.pipeline import GesturePipeline
from ergosense.gestures.worker import GestureWorker
from ergosense.monitoring.activity_period import ActivityPeriod
from ergosense.monitoring.activity_recorder import ActivityRecorder
from ergosense.monitoring.inactivity import InactivityMonitor
from ergosense.monitoring.input_listener import InputListener
from ergosense.ui.auth_dialogs import LoginDialog
from ergosense.ui.main_window import MainWindow
from ergosense.ui.settings_dialog import SettingsDialog


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
    override = os.environ.get("ERGOSENSE_INACTIVITY_SECONDS")
    inactivity_override = int(override) if override else None
    inactivity = InactivityMonitor(
        time.monotonic,
        lambda: datetime.now(UTC),
        inactivity_override or settings["inactivity_break_minutes"] * 60,
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

    # Control por gestos (PB-07 a PB-13): un hilo lee la cámara y mueve el cursor;
    # los clicks y el scroll pasan por el ejecutor único de acciones.
    mouse = MouseActions()
    executor = ActionExecutor(mouse.perform)
    executor.start()
    gestures = GestureWorker(
        Camera(),
        HandTracker,
        GesturePipeline(primary_screen(), time.monotonic),
        mouse,
        executor,
        on_activity=register_activity,
    )
    # Las señales llegan desde el hilo de gestos; Qt las entrega en el de la ventana.
    gestures.gesture_changed.connect(window.show_gesture)
    gestures.camera_unavailable.connect(window.show_camera_unavailable)
    # Se respeta la preferencia guardada en la cuenta (PB-36): la cámara solo se abre
    # si el control por gestos está activado.
    preferences = PreferencesController(
        gestures, inactivity, window, inactivity_override=inactivity_override
    )
    preferences.apply(settings)

    def open_settings():
        """Abre la configuración y, si se guardó, la aplica sin reiniciar (PB-37)."""
        dialog = SettingsDialog(api_client, window)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            preferences.apply(api_client.settings)

    window.settings_requested.connect(open_settings)

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
        # Primero los gestos: sueltan el botón si había un arrastre y liberan la
        # cámara; después el ejecutor termina las acciones pendientes.
        gestures.stop()
        executor.stop()
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
