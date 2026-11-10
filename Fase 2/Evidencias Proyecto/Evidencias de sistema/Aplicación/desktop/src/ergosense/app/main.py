"""Punto de entrada de ErgoSense: integra monitoreo, gestos, voz y preferencias."""

import os
import sys
import time
from datetime import UTC, datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QMessageBox,
    QSystemTrayIcon,
)

from ergosense.actions.executor import ActionExecutor
from ergosense.actions.mouse import MouseActions
from ergosense.actions.screen import primary_screen
from ergosense.api_client import ApiClient, ApiClientError
from ergosense.api_client.pending import PendingQueue
from ergosense.app.controller import MonitorController
from ergosense.app.preferences import PreferencesController
from ergosense.app.remote_session import RemoteUsageSession
from ergosense.gestures.camera import Camera
from ergosense.gestures.hand_tracker import HandTracker
from ergosense.gestures.pipeline import GesturePipeline
from ergosense.gestures.worker import GestureWorker
from ergosense.macros.controller import MacroController
from ergosense.macros.library import MacroLibrary
from ergosense.macros.runner import ActionRunner
from ergosense.monitoring.activity_period import ActivityPeriod
from ergosense.monitoring.activity_recorder import ActivityRecorder
from ergosense.monitoring.inactivity import InactivityMonitor
from ergosense.monitoring.input_listener import InputListener
from ergosense.ui import icons
from ergosense.ui.auth_dialogs import LoginDialog
from ergosense.ui.macros_dialog import ApplicationsDialog, MacrosDialog
from ergosense.ui.main_window import MainWindow
from ergosense.ui.settings_dialog import SettingsDialog
from ergosense.ui.theme import apply_theme
from ergosense.voice.controller import VoiceController
from ergosense.voice.worker import VoiceWorker

# Mensaje breve que confirma cada cambio hecho desde los interruptores.
FEATURE_MESSAGES = {
    ("gesture_enabled", True): "Control con la mano activado.",
    ("gesture_enabled", False): "Control con la mano desactivado.",
    ("voice_enabled", True): "Control por voz activado.",
    ("voice_enabled", False): "Control por voz desactivado.",
}


def main():
    """Inicia la aplicación y devuelve su código de salida al cerrar la ventana."""
    app = QApplication(sys.argv)
    # Colores, tipografía y logo de ErgoSense en todas las ventanas (Sprint 04).
    apply_theme(app)
    app.setWindowIcon(icons.app_icon())

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
    tray = QSystemTrayIcon(icons.app_icon())
    tray.setToolTip("ErgoSense")
    tray.show()

    window = MainWindow(tray)
    window.show_user(api_client.user["name"], api_client.user["email"])
    window.show_connection(True)

    # Pérdida de conexión (PB-50): los registros esperan en memoria y se envían al
    # reconectar; mientras tanto, se consulta el servidor cada 30 segundos.
    def connection_changed(online):
        window.show_connection(online)
        if online:
            window.show_toast("Se recuperó la conexión con el servidor.")
        else:
            window.show_toast(
                "Sin conexión con el servidor. ErgoSense sigue funcionando y guardará "
                "los registros al reconectar.",
                "error",
            )

    pending = PendingQueue(
        api_client.check_connection, time.monotonic, connection_changed,
        on_rejected=lambda error: window.show_toast(
            f"El servidor rechazó un registro pendiente: {error}", "error"
        ),
    )
    remote_session = RemoteUsageSession(api_client, queue=pending)
    remote_session.start()

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
    # El mismo ejecutor atiende los clicks de gestos y voz y los pasos de las macros.
    runner = ActionRunner(
        mouse, on_error=lambda message: macro_controller.report_error(message)
    )
    executor = ActionExecutor(
        runner.perform,
        on_error=lambda error: macro_controller.report_error(
            "No se pudo ejecutar la acción. Comprueba la aplicación de destino."
        ),
    )
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
    gestures.hand_changed.connect(window.show_hand)
    gestures.frame_ready.connect(window.show_frame)
    # Se respeta la preferencia guardada en la cuenta (PB-36): la cámara solo se abre
    # si el control por gestos está activado.
    voice = VoiceWorker()
    voice.status_changed.connect(window.show_voice_status)
    voice.microphone_changed.connect(window.show_microphone)
    preferences = PreferencesController(
        gestures,
        inactivity,
        window,
        inactivity_override=inactivity_override,
        voice=voice,
    )
    preferences.apply(settings)

    def update_features(changes, message=None):
        """Guarda un cambio de gestos o voz y lo aplica; devuelve True si resultó."""
        try:
            if not pending.online:
                raise ApiClientError("Sin conexión.")  # no se espera otro intento
            updated = api_client.update_settings(changes)
        except ApiClientError as error:
            if error.status_code is not None:
                # El servidor lo rechazó: se vuelve a mostrar lo guardado en la cuenta.
                preferences.apply(api_client.settings)
                window.show_toast(str(error), "error")
                return False
            # Sin conexión (PB-50): el cambio se aplica y se guarda al reconectar.
            pending.report_offline()
            api_client.settings = {**api_client.settings, **changes}
            pending.submit(lambda: api_client.update_settings(changes))
            updated = api_client.settings
        preferences.apply(updated)
        if message:
            window.show_toast(message)
        return True

    # Macros (PB-38 a PB-45): se cargan al iniciar y quedan en memoria.
    library = MacroLibrary(api_client)
    library.subscribe(lambda: voice.set_macro_phrases(library.voice_phrases()))
    try:
        library.load()
    except ApiClientError as error:
        window.show_toast(f"No se pudieron cargar las macros. {error}", "error")
    macro_controller = MacroController(
        library,
        executor,
        lambda: api_client.settings.get("voice_enabled") and voice.running,
        lambda: (
            api_client.settings.get("gesture_enabled")
            and gestures.running
            and gestures.actions_enabled
        ),
        register_activity,
    )
    gestures.gesture_changed.connect(macro_controller.handle_gesture)
    macro_controller.failed.connect(lambda message: window.show_toast(message, "error"))
    asking = False

    def ask_to_register(name):
        """Una acción OPEN_APP sin aplicación en este computador (PB-41)."""
        nonlocal asking
        if asking:
            return
        asking = True
        answer = QMessageBox.question(
            window,
            "Registrar aplicación",
            f"La macro necesita la aplicación «{name}», que no está registrada en "
            "este computador. ¿Quieres registrarla ahora?",
        )
        if answer == QMessageBox.StandardButton.Yes:
            ApplicationsDialog(library, name, window).exec()
        asking = False

    macro_controller.application_missing.connect(ask_to_register)
    window.macros_requested.connect(lambda: MacrosDialog(library, window).exec())

    voice_controller = VoiceController(
        lambda: api_client.settings.get("voice_enabled") and voice.running,
        executor,
        update_features,
        register_activity,
        run_macro=macro_controller.handle_voice,
    )
    voice.recognized.connect(voice_controller.handle)
    window.feature_requested.connect(
        lambda key, value: update_features({key: value}, FEATURE_MESSAGES[key, value])
    )

    def set_camera(on):
        """Enciende la cámara solo para la vista previa, o la apaga."""
        if on:
            preferences.start_camera()
            return
        gestures_were_on = api_client.settings.get("gesture_enabled")
        preferences.stop_camera()
        # Sin cámara no hay control con la mano: también se desactiva en la cuenta.
        if gestures_were_on and update_features({"gesture_enabled": False}):
            window.show_toast("La cámara y el control con la mano se han desactivado.")

    window.camera_requested.connect(set_camera)

    def open_settings():
        """Abre la configuración y, si se guardó, la aplica sin reiniciar (PB-37)."""
        dialog = SettingsDialog(api_client, window)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            preferences.apply(api_client.settings)
            window.show_toast("Preferencias guardadas.")

    window.settings_requested.connect(open_settings)

    # El timer corre en el hilo principal: es el único que actualiza la ventana.
    timer = QTimer()
    timer.timeout.connect(controller.tick)
    timer.timeout.connect(pending.poll)
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
        voice.stop()
        executor.stop()
        listener.stop()
        try:
            controller.finish()
            # Último intento de enviar los registros pendientes (arquitectura, 5.6).
            pending.retry_now()
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
