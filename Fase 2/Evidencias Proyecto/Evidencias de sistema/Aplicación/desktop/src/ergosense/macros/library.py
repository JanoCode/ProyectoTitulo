"""Macros y aplicaciones de la cuenta, guardadas en el servidor (PB-38 a PB-45).

Al iniciar sesión se descargan las macros de la cuenta y las aplicaciones de este
computador, y quedan en memoria: así las macros siguen funcionando aunque se
pierda la conexión (PB-50). Cada cambio se guarda primero en el servidor y,
solo si este lo acepta, se actualiza la copia en memoria.
"""

import platform

from ergosense.macros import catalog
from ergosense.voice.commands import normalize


def device_name():
    """Nombre de equipo de Windows: identifica el computador actual (PB-41)."""
    return platform.node()


def _uses(macro, trigger_type, key):
    return any(
        trigger["trigger_type"] == trigger_type
        and normalize(trigger["trigger_value"]) == key
        for trigger in macro["triggers"]
    )


class MacroLibrary:
    def __init__(self, api_client, device=None):
        self._api = api_client
        self.device = device or device_name()
        self.macros = []
        self.applications = []
        self._listeners = []

    def subscribe(self, listener):
        """listener() se llama cada vez que cambian las macros o las aplicaciones."""
        self._listeners.append(listener)

    def load(self):
        """Descarga las macros de la cuenta y las aplicaciones del equipo (SB05-T23)."""
        macros = list(self._api.list_macros())
        applications = list(self._api.list_applications(self.device))
        self.macros, self.applications = macros, applications
        self._changed()

    # ---------- macros

    def save_macro(self, data, macro_id=None):
        """Crea la macro o la reemplaza; devuelve la versión guardada."""
        if macro_id is None:
            saved = self._api.create_macro(data)
        else:
            saved = self._api.replace_macro(macro_id, data)
        self._put_macro(saved)
        return saved

    def set_enabled(self, macro_id, enabled):
        self._put_macro(self._api.set_macro_enabled(macro_id, enabled))

    def delete_macro(self, macro_id):
        self._api.delete_macro(macro_id)
        self.macros = [macro for macro in self.macros if macro["id"] != macro_id]
        self._changed()

    def find(self, trigger_type, value):
        """Macro activada que usa ese activador, o None (PB-42 y PB-43)."""
        key = normalize(value)
        for macro in self.macros:
            if macro["enabled"] and _uses(macro, trigger_type, key):
                return macro
        return None

    def voice_phrases(self):
        """Frases de las macros activadas, para la gramática de la voz."""
        return tuple(
            trigger["trigger_value"]
            for macro in self.macros
            if macro["enabled"]
            for trigger in macro["triggers"]
            if trigger["trigger_type"] == "VOICE"
        )

    def trigger_problem(self, trigger_type, value, macro_id=None):
        """Motivo por el que no se puede usar el activador, o None (PB-44).

        La interfaz lo usa para informar el conflicto de inmediato; la API vuelve a
        validarlo al guardar.
        """
        problem = catalog.trigger_problem(trigger_type, value)
        if problem:
            return problem
        key = normalize(value)
        for macro in self.macros:
            if macro["id"] != macro_id and _uses(macro, trigger_type, key):
                return f"Ese activador ya está asignado a la macro «{macro['name']}»."
        return None

    # ---------- aplicaciones de este computador (PB-41)

    def application_path(self, name):
        """Ruta de la aplicación registrada con ese nombre en este equipo, o None."""
        for application in self.applications:
            if application["name"].casefold() == name.strip().casefold():
                return application["executable_path"]
        return None

    def save_application(self, name, path, application_id=None):
        data = {"device_name": self.device, "name": name, "executable_path": path}
        if application_id is None:
            saved = self._api.create_application(data)
        else:
            saved = self._api.update_application(application_id, data)
        others = [app for app in self.applications if app["id"] != saved["id"]]
        self.applications = sorted(
            [*others, saved], key=lambda app: app["name"].casefold()
        )
        self._changed()
        return saved

    def delete_application(self, application_id):
        self._api.delete_application(application_id)
        self.applications = [
            app for app in self.applications if app["id"] != application_id
        ]
        self._changed()

    def _put_macro(self, saved):
        others = [macro for macro in self.macros if macro["id"] != saved["id"]]
        self.macros = sorted([*others, saved], key=lambda macro: macro["id"])
        self._changed()

    def _changed(self):
        for listener in self._listeners:
            listener()
