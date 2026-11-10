"""Pruebas de las macros (Sprint 05: PB-38 a PB-44), sin servidor ni hardware."""

import pytest
from PySide6.QtWidgets import QApplication

from ergosense.actions.action import Action
from ergosense.macros import catalog
from ergosense.macros.controller import MacroController
from ergosense.macros.library import MacroLibrary
from ergosense.macros.runner import ActionRunner, MacroStep
from ergosense.voice.controller import VoiceController
from ergosense.voice.grammar import phrases

MAIL = {
    "id": 1,
    "name": "Abrir correo",
    "enabled": True,
    "triggers": [{"trigger_type": "VOICE", "trigger_value": "abrir correo"}],
    # Llegan desordenadas a propósito: se ejecutan según execution_order.
    "actions": [
        {"action_type": "KEY_PRESS", "action_value": "ctrl+t", "execution_order": 2},
        {
            "action_type": "OPEN_URL",
            "action_value": "https://mail.com",
            "execution_order": 1,
        },
    ],
}
NOTES = {
    "id": 2,
    "name": "Notas",
    "enabled": True,
    "triggers": [{"trigger_type": "GESTURE", "trigger_value": "fist"}],
    "actions": [
        {
            "action_type": "OPEN_APP",
            "action_value": "Bloc de notas",
            "execution_order": 1,
        },
        {"action_type": "TYPE_TEXT", "action_value": "Hola", "execution_order": 2},
    ],
}


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


class FakeApi:
    """Servidor falso: devuelve lo que recibe, como lo haría la API."""

    def __init__(self, macros=(), applications=()):
        self.macros = [dict(macro) for macro in macros]
        self.applications = list(applications)
        self.devices = []

    def list_macros(self):
        return self.macros

    def list_applications(self, device):
        self.devices.append(device)
        return self.applications

    def set_macro_enabled(self, macro_id, enabled):
        macro = next(m for m in self.macros if m["id"] == macro_id)
        macro["enabled"] = enabled
        return dict(macro)

    def create_macro(self, data):
        return {"id": 99, **data}


class FakeExecutor:
    def __init__(self):
        self.submitted = []

    def submit(self, action):
        self.submitted.append(action)

    def submit_batch(self, actions):
        self.submitted.extend(actions)


def make(voice=True, gestures=True, applications=()):
    library = MacroLibrary(FakeApi([MAIL, NOTES], applications), device="PC-PRUEBA")
    library.load()
    executor = FakeExecutor()
    controller = MacroController(
        library, executor, lambda: voice, lambda: gestures, lambda: None
    )
    return library, executor, controller


# ---------- catálogo y validación (PB-39, PB-40, PB-44)


def test_cp_05_14_no_permite_comandos_base_ni_gestos_predefinidos():
    assert "comando" in catalog.trigger_problem("VOICE", "Clic  Izquierdo")
    assert "predefinida" in catalog.trigger_problem("GESTURE", "thumb_in")
    assert catalog.trigger_problem("GESTURE", "fist") is None
    assert catalog.trigger_problem("VOICE", "abrir música") is None


def test_cp_05_13_informa_el_activador_que_usa_otra_macro():
    library, *_ = make()
    problem = library.trigger_problem("VOICE", "Abrír Correo")
    assert problem == "Ese activador ya está asignado a la macro «Abrir correo»."
    # Al editar la misma macro, puede conservar su activador.
    assert library.trigger_problem("VOICE", "abrir correo", macro_id=1) is None


@pytest.mark.parametrize(
    ("kind", "value", "valid"),
    [
        ("OPEN_URL", "https://duoc.cl", True),
        ("OPEN_URL", "www.duoc.cl", False),
        ("KEY_PRESS", "ctrl+shift+t", True),
        ("KEY_PRESS", "alt+f4", True),
        ("KEY_PRESS", "ctrl+", False),
        ("KEY_PRESS", "shift+ctrl", False),  # falta la tecla final
        ("TYPE_TEXT", "Hola", True),
        ("TYPE_TEXT", "", False),
        ("MOUSE_CLICK", "double", True),
        ("MOUSE_CLICK", "middle", False),
        ("OPEN_APP", "Bloc de notas", True),
        ("RUN_SCRIPT", "algo", False),
    ],
)
def test_cp_05_05_solo_acepta_los_tipos_y_valores_soportados(kind, value, valid):
    assert (catalog.action_problem(kind, value) is None) is valid


def test_el_catalogo_coincide_con_los_gestos_y_comandos_de_la_aplicacion():
    assert set(catalog.MACRO_GESTURES) == {"fist", "l_shape"}
    assert "activar gestos y voz" in catalog.BASE_VOICE_COMMANDS


# ---------- ejecución (PB-42 y PB-43)


def test_cp_05_09_la_frase_ejecuta_las_acciones_en_orden():
    _, executor, controller = make()
    assert controller.handle_voice("abrir correo") is True
    assert [step.action_type for step in executor.submitted] == [
        "OPEN_URL",
        "KEY_PRESS",
    ]


def test_cp_05_10_el_gesto_ejecuta_la_macro_con_la_ruta_de_este_equipo():
    app = {"id": 5, "name": "Bloc de notas", "executable_path": r"C:\notepad.exe"}
    _, executor, controller = make(applications=[app])
    controller.handle_gesture("fist")
    assert executor.submitted == [
        MacroStep("OPEN_APP", r"C:\notepad.exe", "Notas"),
        MacroStep("TYPE_TEXT", "Hola", "Notas"),
    ]


def test_cp_05_08_sin_la_aplicacion_en_este_equipo_pide_registrarla(qapp):
    _, executor, controller = make()
    missing = []
    controller.application_missing.connect(missing.append)
    controller.handle_gesture("fist")
    assert missing == ["Bloc de notas"]
    assert executor.submitted == []


def test_cp_05_11_con_el_control_desactivado_no_se_ejecuta():
    _, executor, controller = make(voice=False, gestures=False)
    assert controller.handle_voice("abrir correo") is False
    controller.handle_gesture("fist")
    assert executor.submitted == []


def test_cp_05_12_una_macro_desactivada_no_se_ejecuta_y_al_reactivarla_si():
    library, executor, controller = make()
    library.set_enabled(1, False)
    assert controller.handle_voice("abrir correo") is False
    library.set_enabled(1, True)
    assert controller.handle_voice("abrir correo") is True
    assert len(executor.submitted) == 2


def test_un_gesto_predefinido_no_busca_macros():
    _, executor, controller = make()
    controller.handle_gesture("thumb_in")
    assert executor.submitted == []


def test_la_voz_resuelve_primero_los_comandos_base():
    _, executor, controller = make()
    voice = VoiceController(
        lambda: True,
        executor,
        lambda changes: None,
        lambda: None,
        controller.handle_voice,
    )
    voice.handle("clic izquierdo")
    voice.handle("abrir correo")
    voice.handle("hola que tal")  # ni comando ni macro: no hace nada
    assert executor.submitted[0] is Action.LEFT_CLICK
    assert len(executor.submitted) == 3


def test_la_gramatica_incluye_solo_las_frases_de_macros_activadas():
    library, *_ = make()
    assert library.voice_phrases() == ("abrir correo",)
    library.set_enabled(1, False)
    assert library.voice_phrases() == ()
    grammar = phrases(["abrir correo"])
    assert "abrir correo" in grammar
    assert "abrir" not in grammar  # sus palabras dejan de ser relleno


def test_avisa_cuando_cambian_las_macros():
    library, *_ = make()
    changes = []
    library.subscribe(lambda: changes.append(True))
    library.set_enabled(1, False)
    library.save_macro(
        {"name": "Nueva", "enabled": True, "triggers": [], "actions": []}
    )
    assert len(changes) == 2
    assert library.macros[-1]["id"] == 99


def test_las_aplicaciones_se_piden_para_este_computador():
    library, *_ = make()
    assert library._api.devices == ["PC-PRUEBA"]


# ---------- cada tipo de acción (SB05-T13)


class FakeKeyboard:
    def __init__(self):
        self.events = []

    def press(self, key):
        self.events.append(("press", key))

    def release(self, key):
        self.events.append(("release", key))

    def type(self, text):
        self.events.append(("type", text))


class FakeMouse:
    def __init__(self):
        self.actions = []

    def perform(self, action):
        self.actions.append(action)


def make_runner(**kwargs):
    mouse, keyboard, opened = FakeMouse(), FakeKeyboard(), []
    runner = ActionRunner(
        mouse,
        keyboard,
        open_url=opened.append,
        start_process=lambda args, cwd: opened.append((args, cwd)),
        **kwargs,
    )
    return runner, mouse, keyboard, opened


def test_ejecuta_cada_tipo_de_accion():
    runner, mouse, keyboard, opened = make_runner()
    runner.perform(MacroStep("OPEN_URL", "https://duoc.cl"))
    runner.perform(MacroStep("OPEN_APP", r"C:\Apps\editor.exe"))
    runner.perform(MacroStep("TYPE_TEXT", "Hola"))
    runner.perform(MacroStep("MOUSE_CLICK", "double"))
    runner.perform(Action.RIGHT_CLICK)  # las acciones de gestos y voz siguen igual
    assert opened == ["https://duoc.cl", ([r"C:\Apps\editor.exe"], r"C:\Apps")]
    assert keyboard.events == [("type", "Hola")]
    assert mouse.actions == [Action.DOUBLE_CLICK, Action.RIGHT_CLICK]


def test_presiona_la_combinacion_y_suelta_las_teclas_en_orden_inverso():
    from pynput.keyboard import Key

    runner, _, keyboard, _ = make_runner()
    runner.perform(MacroStep("KEY_PRESS", "ctrl+shift+t"))
    assert keyboard.events == [
        ("press", Key.ctrl),
        ("press", Key.shift),
        ("press", "t"),
        ("release", "t"),
        ("release", Key.shift),
        ("release", Key.ctrl),
    ]


def test_si_no_puede_abrir_la_aplicacion_avisa_y_no_se_cae():
    errors = []

    def missing(args, cwd):
        raise FileNotFoundError(args[0])

    runner = ActionRunner(
        FakeMouse(), FakeKeyboard(), start_process=missing, on_error=errors.append
    )
    runner.perform(MacroStep("OPEN_APP", r"C:\no-existe.exe", "Notas"))
    assert errors == [r"La macro «Notas» no pudo abrir C:\no-existe.exe."]


def test_modifier_is_released_when_the_next_press_fails():
    from pynput.keyboard import Key

    class BrokenKeyboard(FakeKeyboard):
        def press(self, key):
            if key == Key.shift:
                raise OSError("Keyboard unavailable")
            super().press(key)

    keyboard = BrokenKeyboard()
    runner = ActionRunner(FakeMouse(), keyboard)
    with pytest.raises(OSError):
        runner._press("ctrl+shift+t")
    assert keyboard.events == [("press", Key.ctrl), ("release", Key.ctrl)]


def test_failed_macro_step_stops_the_batch_but_not_later_actions():
    from ergosense.actions.executor import ActionExecutor

    errors = []
    keyboard = FakeKeyboard()
    runner = ActionRunner(FakeMouse(), keyboard, open_url=lambda url: False,
                          on_error=errors.append)
    executor = ActionExecutor(runner.perform)
    executor.start()
    executor.submit_batch([
        MacroStep("OPEN_URL", "https://duoc.cl", "Correo"),
        MacroStep("TYPE_TEXT", "No escribir"),
    ])
    executor.submit(MacroStep("TYPE_TEXT", "Nueva acción"))
    executor.stop()
    assert keyboard.events == [("type", "Nueva acción")]
    assert len(errors) == 1
