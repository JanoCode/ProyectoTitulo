"""Pruebas de la escucha de teclado y mouse (Sprint 01: PB-02 y PB-03)."""

from ergosense.monitoring.input_listener import InputListener


def make_listener():
    calls = []
    listener = InputListener(on_activity=lambda: calls.append("actividad"))
    return listener, calls


def test_cp_01_03_una_tecla_cuenta_como_actividad():
    listener, calls = make_listener()
    listener._on_press(
        "a"
    )  # hay seguiridad ya que le pasa la tecla pero no la recibe por ende no la guarda como tal
    assert calls == ["actividad"]


def test_cp_01_04_un_click_cuenta_como_actividad():
    listener, calls = make_listener()
    listener._on_click(100, 200, "left", True)
    assert calls == ["actividad"]


def test_cp_01_05_soltar_el_boton_no_duplica_la_actividad():
    listener, calls = make_listener()
    listener._on_click(100, 200, "left", True)  # presionar
    listener._on_click(100, 200, "left", False)  # soltar
    assert calls == ["actividad"]


def test_cp_02_12_el_scroll_cuenta_como_actividad():
    listener, calls = make_listener()
    listener._on_scroll(100, 200, 0, -1)
    assert calls == ["actividad"]


def test_cp_02_12_mover_el_mouse_cuenta_como_actividad():
    listener, calls = make_listener()
    listener._on_move(100, 200)
    assert calls == ["actividad"]
