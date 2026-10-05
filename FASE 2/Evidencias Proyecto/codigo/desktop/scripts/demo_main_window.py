"""Prueba manual: abre la ventana con datos de ejemplo."""

import sys

from PySide6.QtWidgets import QApplication

from ergosense.ui.main_window import MainWindow

app = QApplication(sys.argv)
window = MainWindow()
window.show_period(125)
window.show_last_activity(3)
window.show()
sys.exit(app.exec())  # mantiene la ventana abierta hasta que la cierres
