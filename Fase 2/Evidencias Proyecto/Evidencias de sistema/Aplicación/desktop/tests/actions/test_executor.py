"""Pruebas del ejecutor único de acciones y del tamaño de la pantalla (Sprint 03)."""

import threading

from ergosense.actions.action import Action
from ergosense.actions.executor import ActionExecutor
from ergosense.actions.screen import primary_screen


def test_ejecuta_las_acciones_en_el_orden_en_que_llegan():
    performed = []
    executor = ActionExecutor(performed.append)
    executor.start()
    executor.submit(Action.LEFT_DOWN)
    executor.submit(Action.SCROLL_UP)
    executor.submit(Action.LEFT_UP)
    executor.stop()  # espera a que se vacíe la cola
    assert performed == [Action.LEFT_DOWN, Action.SCROLL_UP, Action.LEFT_UP]


def test_las_acciones_corren_en_otro_hilo():
    threads = []
    executor = ActionExecutor(lambda action: threads.append(threading.current_thread()))
    executor.start()
    executor.submit(Action.LEFT_CLICK)
    executor.stop()
    assert threads[0].name == "acciones"


def test_detener_sin_haber_iniciado_no_falla():
    ActionExecutor(lambda action: None).stop()


def test_el_monitor_principal_empieza_en_el_origen_y_tiene_tamano():
    left, top, width, height = primary_screen()
    assert (left, top) == (0, 0)
    assert width > 0
    assert height > 0
