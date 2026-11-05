"""Casos CP-05-03 a CP-05-07, CP-05-12 a CP-05-14: macros y aplicaciones."""

import pytest

from app.models import MacroAction, MacroTrigger
from tests.test_settings import bearer, create_account_and_token

MACROS = "/api/v1/macros"
APPLICATIONS = "/api/v1/applications"


def macro(name="Abrir correo", triggers=None, actions=None, **extra):
    return {
        "name": name,
        "triggers": triggers
        or [{"trigger_type": "VOICE", "trigger_value": "abrir correo"}],
        "actions": actions
        or [
            {"action_type": "OPEN_URL", "action_value": "https://mail.google.com"},
            {"action_type": "KEY_PRESS", "action_value": "ctrl+shift+t"},
        ],
        **extra,
    }


@pytest.fixture
def headers(client):
    return bearer(create_account_and_token(client, "macros@example.com"))


def test_cp_05_01_crea_una_macro_activada_y_la_lista(client, headers):
    created = client.post(MACROS, headers=headers, json=macro(description=" Correo "))

    assert created.status_code == 201
    body = created.json()
    assert body["enabled"] is True  # una nueva macro queda activada (PB-38)
    assert body["description"] == "Correo"
    assert client.get(MACROS, headers=headers).json() == [body]


def test_cp_05_03_guarda_la_frase_como_activador_de_voz(client, headers):
    triggers = [{"trigger_type": "VOICE", "trigger_value": "  Abrir   Música "}]
    body = client.post(MACROS, headers=headers, json=macro(triggers=triggers)).json()

    # Se guarda en minúsculas y con espacios simples, conservando las tildes.
    assert body["triggers"] == [
        {"trigger_type": "VOICE", "trigger_value": "abrir música"}
    ]


def test_cp_05_04_guarda_el_gesto_como_activador_de_gesto(client, headers):
    triggers = [
        {"trigger_type": "GESTURE", "trigger_value": "fist"},
        {"trigger_type": "VOICE", "trigger_value": "abrir correo"},
    ]
    body = client.post(MACROS, headers=headers, json=macro(triggers=triggers)).json()

    assert body["triggers"][0] == {"trigger_type": "GESTURE", "trigger_value": "fist"}
    assert len(body["triggers"]) == 2  # una macro puede tener más de un activador


@pytest.mark.parametrize(
    ("action_type", "value"),
    [
        ("RUN_SCRIPT", "format c:"),
        ("OPEN_URL", "ftp://servidor"),
        ("OPEN_URL", "javascript:alert(1)"),
        ("KEY_PRESS", "ctrl+banana"),
        ("KEY_PRESS", "ctrl+ctrl+t"),
        ("TYPE_TEXT", "   "),
        ("TYPE_TEXT", "x" * 501),
        ("MOUSE_CLICK", "middle"),
        ("OPEN_APP", " "),
    ],
)
def test_cp_05_05_solo_acepta_los_cinco_tipos_de_accion(
    client, headers, action_type, value
):
    actions = [{"action_type": action_type, "action_value": value}]

    response = client.post(MACROS, headers=headers, json=macro(actions=actions))

    assert response.status_code == 422
    assert client.get(MACROS, headers=headers).json() == []


def test_cp_05_05_acepta_cada_tipo_soportado(client, headers):
    actions = [
        {"action_type": "OPEN_URL", "action_value": "https://duoc.cl"},
        {"action_type": "OPEN_APP", "action_value": "Bloc de notas"},
        {"action_type": "KEY_PRESS", "action_value": "ctrl+alt+f4"},
        {"action_type": "TYPE_TEXT", "action_value": " Hola, equipo "},
        {"action_type": "MOUSE_CLICK", "action_value": "double"},
    ]

    body = client.post(MACROS, headers=headers, json=macro(actions=actions)).json()

    assert [action["action_type"] for action in body["actions"]] == [
        "OPEN_URL",
        "OPEN_APP",
        "KEY_PRESS",
        "TYPE_TEXT",
        "MOUSE_CLICK",
    ]
    assert body["actions"][3]["action_value"] == " Hola, equipo "


def test_cp_05_06_guarda_el_orden_y_permite_modificarlo(client, headers):
    created = client.post(MACROS, headers=headers, json=macro()).json()
    reordered = macro(actions=list(reversed(macro()["actions"])))

    response = client.put(f"{MACROS}/{created['id']}", headers=headers, json=reordered)

    actions = response.json()["actions"]
    assert [a["action_type"] for a in actions] == ["KEY_PRESS", "OPEN_URL"]
    assert [a["execution_order"] for a in actions] == [1, 2]


def test_cp_05_02_editar_reemplaza_y_eliminar_borra_activadores_y_acciones(
    client, headers, database
):
    created = client.post(MACROS, headers=headers, json=macro()).json()
    edited = macro(
        name="Correo",
        triggers=[{"trigger_type": "GESTURE", "trigger_value": "l_shape"}],
    )

    updated = client.put(
        f"{MACROS}/{created['id']}", headers=headers, json=edited
    ).json()
    assert updated["name"] == "Correo"
    assert updated["triggers"] == [
        {"trigger_type": "GESTURE", "trigger_value": "l_shape"}
    ]
    assert database.query(MacroTrigger).count() == 1  # el activador anterior se borró

    deleted = client.delete(f"{MACROS}/{created['id']}", headers=headers)
    assert deleted.status_code == 204
    assert database.query(MacroTrigger).count() == 0
    assert database.query(MacroAction).count() == 0


def test_cp_05_12_activa_y_desactiva_sin_modificar_la_macro(client, headers):
    created = client.post(MACROS, headers=headers, json=macro()).json()

    off = client.patch(
        f"{MACROS}/{created['id']}", headers=headers, json={"enabled": False}
    )

    assert off.json()["enabled"] is False
    assert off.json()["actions"] == created["actions"]
    # El estado se conserva en el servidor al reiniciar la aplicación (PB-43).
    assert client.get(MACROS, headers=headers).json()[0]["enabled"] is False


@pytest.mark.parametrize("phrase", ["abrir correo", "ABRIR  CORREO", "abrír correo"])
def test_cp_05_13_no_guarda_una_frase_que_ya_usa_otra_macro(client, headers, phrase):
    client.post(MACROS, headers=headers, json=macro())
    triggers = [{"trigger_type": "VOICE", "trigger_value": phrase}]

    response = client.post(MACROS, headers=headers, json=macro("Otra", triggers))

    assert response.status_code == 409
    assert "Abrir correo" in response.json()["detail"]
    assert len(client.get(MACROS, headers=headers).json()) == 1


def test_cp_05_13_no_repite_un_gesto_entre_macros_ni_dentro_de_una(client, headers):
    fist = {"trigger_type": "GESTURE", "trigger_value": "fist"}
    client.post(MACROS, headers=headers, json=macro(triggers=[fist]))

    other = client.post(MACROS, headers=headers, json=macro("Otra", [fist]))
    repeated = client.post(
        MACROS,
        headers=headers,
        json=macro("Doble", [{"trigger_type": "VOICE", "trigger_value": "hola"}] * 2),
    )

    assert other.status_code == 409
    assert repeated.status_code == 409


def test_cp_05_13_al_editar_una_macro_puede_conservar_sus_activadores(client, headers):
    created = client.post(MACROS, headers=headers, json=macro()).json()

    response = client.put(
        f"{MACROS}/{created['id']}", headers=headers, json=macro("Nuevo")
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    "trigger",
    [
        {"trigger_type": "VOICE", "trigger_value": "clic izquierdo"},
        {"trigger_type": "VOICE", "trigger_value": "Desactivar  Gestos"},
        {"trigger_type": "GESTURE", "trigger_value": "thumb_in"},
        {"trigger_type": "GESTURE", "trigger_value": "point"},
    ],
)
def test_cp_05_14_rechaza_comandos_base_y_gestos_predefinidos(client, headers, trigger):
    response = client.post(MACROS, headers=headers, json=macro(triggers=[trigger]))

    assert response.status_code == 409
    assert client.get(MACROS, headers=headers).json() == []


@pytest.mark.parametrize(
    "trigger",
    [
        {"trigger_type": "GESTURE", "trigger_value": "pulgar arriba"},
        {"trigger_type": "VOICE", "trigger_value": "abrir 123"},
        {"trigger_type": "CLAP", "trigger_value": "dos aplausos"},
    ],
)
def test_cp_05_04_rechaza_activadores_no_reconocidos(client, headers, trigger):
    response = client.post(MACROS, headers=headers, json=macro(triggers=[trigger]))

    assert response.status_code == 422


def test_el_nombre_es_obligatorio(client, headers):
    assert (
        client.post(MACROS, headers=headers, json=macro(name="  ")).status_code == 422
    )


def test_cada_cuenta_ve_y_modifica_solo_sus_macros(client, headers):
    created = client.post(MACROS, headers=headers, json=macro()).json()
    other = bearer(create_account_and_token(client, "otra-macro@example.com"))

    assert client.get(MACROS, headers=other).json() == []
    assert client.delete(f"{MACROS}/{created['id']}", headers=other).status_code == 404
    # Otra cuenta puede usar la misma frase: la unicidad es por usuario.
    assert client.post(MACROS, headers=other, json=macro()).status_code == 201


# ---------- aplicaciones registradas (PB-41)


def application(device="PC-CASA", name="Bloc de notas", path=r"C:\Windows\notepad.exe"):
    return {"device_name": device, "name": name, "executable_path": path}


def test_cp_05_07_registra_una_aplicacion_por_computador(client, headers):
    created = client.post(APPLICATIONS, headers=headers, json=application())
    client.post(APPLICATIONS, headers=headers, json=application(device="PC-DUOC"))

    listed = client.get(
        APPLICATIONS, headers=headers, params={"device_name": "PC-CASA"}
    )

    assert created.status_code == 201
    assert listed.json() == [created.json()]


def test_no_repite_el_nombre_de_una_aplicacion_en_el_mismo_computador(client, headers):
    client.post(APPLICATIONS, headers=headers, json=application())

    response = client.post(
        APPLICATIONS, headers=headers, json=application(path="D:/x.exe")
    )

    assert response.status_code == 409


@pytest.mark.parametrize("field", ["name", "executable_path", "device_name"])
def test_nombre_y_ruta_son_obligatorios(client, headers, field):
    data = application() | {field: "   "}

    assert client.post(APPLICATIONS, headers=headers, json=data).status_code == 422


def test_modifica_y_elimina_una_aplicacion(client, headers):
    created = client.post(APPLICATIONS, headers=headers, json=application()).json()
    url = f"{APPLICATIONS}/{created['id']}"

    updated = client.put(url, headers=headers, json=application(path="D:/notepad.exe"))
    assert updated.json()["executable_path"] == "D:/notepad.exe"
    assert client.delete(url, headers=headers).status_code == 204
    assert (
        client.get(
            APPLICATIONS, headers=headers, params={"device_name": "PC-CASA"}
        ).json()
        == []
    )


def test_una_cuenta_no_modifica_aplicaciones_de_otra(client, headers):
    created = client.post(APPLICATIONS, headers=headers, json=application()).json()
    other = bearer(create_account_and_token(client, "otra-app@example.com"))

    response = client.put(
        f"{APPLICATIONS}/{created['id']}", headers=other, json=application()
    )

    assert response.status_code == 404
