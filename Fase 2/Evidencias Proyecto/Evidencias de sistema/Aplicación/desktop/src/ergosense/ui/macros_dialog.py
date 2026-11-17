"""Sección de macros: listado, editor y aplicaciones registradas (PB-38 a PB-44).

Cada cambio se guarda en el servidor a través de MacroLibrary. Los problemas de
los activadores y las acciones se informan antes de guardar (SB05-T19); la API
los vuelve a validar y, si rechaza algo, se muestra su mensaje.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ergosense.api_client import ApiClientError
from ergosense.macros import catalog
from ergosense.ui import icons, theme
from ergosense.ui.auth_dialogs import make_error_label
from ergosense.ui.widgets import InfoBox, ToggleSwitch, button, divider, label

TRIGGER_NAMES = {"VOICE": "Frase de voz", "GESTURE": "Gesto"}
PLACEHOLDERS = {
    "OPEN_URL": "https://...",
    "KEY_PRESS": "Por ejemplo: ctrl+shift+t",
    "TYPE_TEXT": "Texto que se escribirá",
}


def _icon_button(name, tooltip):
    widget = QPushButton()
    widget.setProperty("variant", "icon")
    widget.setIcon(icons.icon(name, theme.TEXT, 16))
    widget.setToolTip(tooltip)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    return widget


def _combo(items, value=None):
    """Lista desplegable de (dato, texto), con el dato elegido."""
    widget = QComboBox()
    widget.setMinimumHeight(36)
    for data, text in items:
        widget.addItem(text, data)
    if value is not None and widget.findData(value) >= 0:
        widget.setCurrentIndex(widget.findData(value))
    return widget


def _dialog_layout(dialog, title, subtitle):
    """Encabezado común: título, explicación y cuerpo con márgenes."""
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    body = QVBoxLayout()
    body.setContentsMargins(22, 20, 22, 16)
    body.setSpacing(8)
    body.addWidget(label(title, "dialogTitle"))
    body.addWidget(label(subtitle, "muted", wrap=True))
    body.addSpacing(6)
    layout.addLayout(body, 1)
    return layout, body


def _footer(layout, *buttons):
    layout.addWidget(divider())
    row = QHBoxLayout()
    row.setContentsMargins(22, 14, 22, 14)
    row.addStretch()
    for widget in buttons:
        row.addWidget(widget)
    layout.addLayout(row)


def _scroll(widget):
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.NoFrame)
    widget.setObjectName("scrollContent")  # fondo transparente (theme.py)
    area.viewport().setAutoFillBackground(False)
    area.setWidget(widget)
    return area


def describe(macro):
    """Resumen de una macro: sus activadores y cuántas acciones tiene."""
    triggers = [
        f"«{t['trigger_value']}»"
        if t["trigger_type"] == "VOICE"
        else catalog.GESTURE_NAMES.get(t["trigger_value"], t["trigger_value"])
        for t in macro["triggers"]
    ]
    count = len(macro["actions"])
    return f"{' · '.join(triggers)}  —  {count} acción{'es' if count != 1 else ''}"


class MacrosDialog(QDialog):
    """Listado de macros con sus opciones para administrarlas (SB05-T03)."""

    def __init__(self, library, parent=None):
        super().__init__(parent)
        self._library = library
        self.setWindowTitle("Macros")
        self.setWindowIcon(icons.app_icon())
        self.resize(620, 520)
        layout, body = _dialog_layout(
            self,
            "Macros",
            "Ejecuta varias acciones seguidas al decir una frase o hacer un gesto. "
            "Se guardan en tu cuenta y están disponibles en cualquier computador.",
        )
        self._list = QVBoxLayout()
        self._list.setSpacing(8)
        holder = QWidget()
        holder.setLayout(self._list)
        body.addWidget(_scroll(holder), 1)
        self.error_label = make_error_label()
        body.addWidget(self.error_label)

        applications = button("Aplicaciones", "secondary", "folder")
        applications.clicked.connect(self.open_applications)
        close = button("Cerrar", "secondary")
        close.clicked.connect(self.accept)
        new = button("Nueva macro", "primary", "plus")
        new.clicked.connect(lambda: self.edit(None))
        _footer(layout, applications, close, new)
        self.refresh()

    def refresh(self):
        while self._list.count():
            item = self._list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self._library.macros:
            empty = label(
                "Aún no tienes macros. Crea una con «Nueva macro».", "muted", wrap=True
            )
            self._list.addWidget(empty)
        for macro in self._library.macros:
            self._list.addWidget(self._row(macro))
        self._list.addStretch()

    def _row(self, macro):
        row = QFrame()
        row.setObjectName("macroRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(14, 10, 10, 10)
        texts = QVBoxLayout()
        texts.setSpacing(2)
        texts.addWidget(label(macro["name"], "fieldLabel"))
        texts.addWidget(label(describe(macro), "small", wrap=True))
        layout.addLayout(texts, 1)
        switch = ToggleSwitch()
        switch.set_checked_silently(macro["enabled"])
        switch.setToolTip("Activar o desactivar la macro")
        switch.clicked.connect(lambda checked: self.set_enabled(macro, checked))
        edit = _icon_button("pencil", "Editar")
        edit.clicked.connect(lambda: self.edit(macro))
        delete = _icon_button("trash", "Eliminar")
        delete.clicked.connect(lambda: self.delete(macro))
        for widget in (switch, edit, delete):
            layout.addWidget(widget)
        return row

    def set_enabled(self, macro, enabled):
        """PB-43: la macro se conserva; solo cambia si se ejecuta o no."""
        self._run(lambda: self._library.set_enabled(macro["id"], enabled))
        self.refresh()

    def edit(self, macro):
        if (
            MacroEditor(self._library, macro, self).exec()
            == QDialog.DialogCode.Accepted
        ):
            self.refresh()

    def delete(self, macro):
        answer = QMessageBox.question(
            self,
            "Eliminar macro",
            f"¿Eliminar la macro «{macro['name']}» con sus activadores y acciones?",
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._run(lambda: self._library.delete_macro(macro["id"]))
            self.refresh()

    def open_applications(self):
        ApplicationsDialog(self._library, parent=self).exec()

    def _run(self, change):
        self.error_label.clear()
        try:
            change()
        except ApiClientError as error:
            self.error_label.setText(str(error))


class TriggerRow(QWidget):
    """Un activador: tipo (voz o gesto) y su frase o gesto."""

    def __init__(self, trigger=None):
        super().__init__()
        trigger = trigger or {"trigger_type": "VOICE", "trigger_value": ""}
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.kind = _combo(TRIGGER_NAMES.items(), trigger["trigger_type"])
        self.kind.setFixedWidth(150)
        self.kind.currentIndexChanged.connect(lambda: self._show_value(""))
        self.remove = _icon_button("x", "Quitar activador")
        self._layout.addWidget(self.kind)
        self.editor = None
        self._show_value(trigger["trigger_value"])
        self._layout.addWidget(self.remove)

    def _show_value(self, value):
        if self.editor is not None:
            self.editor.deleteLater()
        if self.kind.currentData() == "VOICE":
            self.editor = QLineEdit(value)
            self.editor.setPlaceholderText("Por ejemplo: abrir correo")
        else:
            items = [(str(g), name) for g, name in catalog.GESTURE_NAMES.items()]
            self.editor = _combo(items, value or None)
        self._layout.insertWidget(1, self.editor, 1)

    def data(self):
        value = (
            self.editor.text()
            if isinstance(self.editor, QLineEdit)
            else self.editor.currentData()
        )
        return {"trigger_type": self.kind.currentData(), "trigger_value": value.strip()}


class ActionRow(QWidget):
    """Una acción: tipo, valor y botones para cambiar su orden."""

    def __init__(self, applications, action=None):
        super().__init__()
        action = action or {"action_type": "OPEN_URL", "action_value": ""}
        self._applications = applications
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.kind = _combo(catalog.ACTION_NAMES.items(), action["action_type"])
        self.kind.setFixedWidth(150)
        self.kind.currentIndexChanged.connect(lambda: self._show_value(""))
        self.up = _icon_button("arrow-up", "Subir")
        self.down = _icon_button("arrow-down", "Bajar")
        self.remove = _icon_button("x", "Quitar acción")
        self._layout.addWidget(self.kind)
        self.editor = None
        self._show_value(action["action_value"])
        for widget in (self.up, self.down, self.remove):
            self._layout.addWidget(widget)

    def _show_value(self, value):
        if self.editor is not None:
            self.editor.deleteLater()
        kind = self.kind.currentData()
        if kind == "MOUSE_CLICK":
            self.editor = _combo(catalog.MOUSE_BUTTONS.items(), value or None)
        elif kind == "OPEN_APP":
            # Se elige una aplicación registrada. Se puede escribir otro nombre: en
            # cada computador se usa la aplicación registrada con ese nombre (PB-41).
            self.editor = _combo([(name, name) for name in self._applications])
            self.editor.setEditable(True)
            self.editor.setCurrentText(value or self.editor.currentText())
        else:
            self.editor = QLineEdit(value)
            self.editor.setPlaceholderText(PLACEHOLDERS[kind])
        self._layout.insertWidget(1, self.editor, 1)

    def data(self):
        editor = self.editor
        if isinstance(editor, QLineEdit):
            value = editor.text()
        elif editor.isEditable():
            value = editor.currentText().strip()
        else:
            value = editor.currentData()
        return {"action_type": self.kind.currentData(), "action_value": value}


class MacroEditor(QDialog):
    """Crea o edita una macro: nombre, activadores y acciones en orden."""

    def __init__(self, library, macro=None, parent=None):
        super().__init__(parent)
        self._library = library
        self._macro_id = macro["id"] if macro else None
        self._enabled = macro["enabled"] if macro else True
        self.setWindowTitle("Editar macro" if macro else "Nueva macro")
        self.setWindowIcon(icons.app_icon())
        self.resize(640, 600)
        layout, body = _dialog_layout(
            self,
            self.windowTitle(),
            "Elige cómo se activa y qué acciones realiza, en orden.",
        )
        content = QWidget()
        form = QVBoxLayout(content)
        form.setContentsMargins(0, 0, 8, 0)
        form.setSpacing(8)
        form.addWidget(label("Nombre", "fieldLabel"))
        self.name_input = QLineEdit(macro["name"] if macro else "")
        form.addWidget(self.name_input)
        form.addWidget(label("Descripción (opcional)", "fieldLabel"))
        self.description_input = QLineEdit((macro or {}).get("description") or "")
        form.addWidget(self.description_input)

        form.addSpacing(6)
        form.addWidget(label("Activadores", "fieldLabel"))
        form.addWidget(
            InfoBox(
                "Usa una frase que no sea un comando de ErgoSense, con palabras "
                "comunes y sus tildes, o el puño o la L. Necesitan la voz o el "
                "control con la mano activados."
            )
        )
        self.triggers = QVBoxLayout()
        form.addLayout(self.triggers)
        add_trigger = button("Agregar activador", "link", "plus", theme.PRIMARY)
        add_trigger.clicked.connect(lambda: self.add_trigger())
        form.addWidget(add_trigger, 0, Qt.AlignmentFlag.AlignLeft)

        form.addSpacing(6)
        form.addWidget(label("Acciones, en el orden en que se ejecutan", "fieldLabel"))
        self.actions = QVBoxLayout()
        form.addLayout(self.actions)
        add_action = button("Agregar acción", "link", "plus", theme.PRIMARY)
        add_action.clicked.connect(lambda: self.add_action())
        form.addWidget(add_action, 0, Qt.AlignmentFlag.AlignLeft)
        form.addStretch()
        body.addWidget(_scroll(content), 1)
        self.error_label = make_error_label()
        body.addWidget(self.error_label)

        for trigger in (macro or {}).get("triggers") or [None]:
            self.add_trigger(trigger)
        for action in (macro or {}).get("actions") or [None]:
            self.add_action(action)

        cancel = button("Cancelar", "secondary")
        cancel.clicked.connect(self.reject)
        save = button("Guardar macro", "primary")
        save.setDefault(True)
        save.clicked.connect(self.submit)
        _footer(layout, cancel, save)

    def add_trigger(self, trigger=None):
        row = TriggerRow(trigger)
        row.remove.clicked.connect(lambda: self._remove(self.triggers, row))
        self.triggers.addWidget(row)

    def add_action(self, action=None):
        names = [app["name"] for app in self._library.applications]
        row = ActionRow(names, action)
        row.remove.clicked.connect(lambda: self._remove(self.actions, row))
        row.up.clicked.connect(lambda: self._move(row, -1))
        row.down.clicked.connect(lambda: self._move(row, 1))
        self.actions.addWidget(row)

    def _remove(self, rows, row):
        rows.removeWidget(row)
        row.deleteLater()

    def _move(self, row, step):
        """Cambia el orden de ejecución de una acción (SB05-T09)."""
        position = self.actions.indexOf(row) + step
        if 0 <= position < self.actions.count():
            self.actions.removeWidget(row)
            self.actions.insertWidget(position, row)

    def _rows(self, rows):
        return [rows.itemAt(index).widget() for index in range(rows.count())]

    def data(self):
        return {
            "name": self.name_input.text().strip(),
            "description": self.description_input.text().strip() or None,
            "enabled": self._enabled,
            "triggers": [row.data() for row in self._rows(self.triggers)],
            "actions": [row.data() for row in self._rows(self.actions)],
        }

    def problem(self, data):
        """Primer problema de la macro, con el motivo en español (SB05-T19)."""
        if not data["name"]:
            return "El nombre de la macro es obligatorio."
        if not data["triggers"]:
            return "Agrega al menos un activador."
        if not data["actions"]:
            return "Agrega al menos una acción."
        seen = set()
        for number, trigger in enumerate(data["triggers"], start=1):
            kind, value = trigger["trigger_type"], trigger["trigger_value"]
            problem = self._library.trigger_problem(kind, value, self._macro_id)
            key = (kind, catalog.clean_phrase(value))
            if problem is None and key in seen:
                problem = "Está repetido en esta macro."
            if problem:
                return f"Activador {number}: {problem}"
            seen.add(key)
        for number, action in enumerate(data["actions"], start=1):
            problem = catalog.action_problem(
                action["action_type"], action["action_value"]
            )
            if problem:
                return f"Acción {number}: {problem}"
        return None

    def submit(self):
        data = self.data()
        problem = self.problem(data)
        if problem:
            self.error_label.setText(problem)
            return
        try:
            self._library.save_macro(data, self._macro_id)
        except ApiClientError as error:
            self.error_label.setText(str(error))
            return
        self.accept()


class ApplicationsDialog(QDialog):
    """Aplicaciones registradas en este computador, con su ruta (PB-41)."""

    def __init__(self, library, name="", parent=None):
        super().__init__(parent)
        self._library = library
        self._editing = None
        self.setWindowTitle("Aplicaciones")
        self.setWindowIcon(icons.app_icon())
        self.resize(560, 480)
        layout, body = _dialog_layout(
            self,
            "Aplicaciones",
            f"Programas que tus macros pueden abrir en este computador "
            f"({library.device}). En otro computador se registran de nuevo, porque "
            f"la ruta cambia.",
        )
        self._list = QVBoxLayout()
        self._list.setSpacing(8)
        holder = QWidget()
        holder.setLayout(self._list)
        body.addWidget(_scroll(holder), 1)

        body.addWidget(label("Nombre", "fieldLabel"))
        self.name_input = QLineEdit(name)
        self.name_input.setPlaceholderText("Por ejemplo: Bloc de notas")
        body.addWidget(self.name_input)
        body.addWidget(label("Ruta del ejecutable", "fieldLabel"))
        path_row = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText(r"C:\Windows\notepad.exe")
        browse = button("Examinar", "secondary", "folder")
        browse.clicked.connect(self.browse)
        path_row.addWidget(self.path_input, 1)
        path_row.addWidget(browse)
        body.addLayout(path_row)
        self.error_label = make_error_label()
        body.addWidget(self.error_label)

        close = button("Cerrar", "secondary")
        close.clicked.connect(self.accept)
        self.save_button = button("Registrar aplicación", "primary", "plus")
        self.save_button.clicked.connect(self.submit)
        _footer(layout, close, self.save_button)
        self.refresh()

    def refresh(self):
        while self._list.count():
            item = self._list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self._library.applications:
            self._list.addWidget(label("Aún no hay aplicaciones registradas.", "muted"))
        for application in self._library.applications:
            row = QFrame()
            row.setObjectName("macroRow")
            line = QHBoxLayout(row)
            line.setContentsMargins(14, 8, 10, 8)
            texts = QVBoxLayout()
            texts.addWidget(label(application["name"], "fieldLabel"))
            texts.addWidget(label(application["executable_path"], "small", wrap=True))
            line.addLayout(texts, 1)
            edit = _icon_button("pencil", "Editar")
            edit.clicked.connect(lambda _=False, app=application: self.start_edit(app))
            delete = _icon_button("trash", "Eliminar")
            delete.clicked.connect(lambda _=False, app=application: self.delete(app))
            line.addWidget(edit)
            line.addWidget(delete)
            self._list.addWidget(row)
        self._list.addStretch()

    def browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Elegir aplicación", "", "Programas (*.exe);;Todos los archivos (*)"
        )
        if path:
            self.path_input.setText(path.replace("/", "\\"))

    def start_edit(self, application):
        self._editing = application["id"]
        self.name_input.setText(application["name"])
        self.path_input.setText(application["executable_path"])
        self.save_button.setText("Guardar cambios")

    def delete(self, application):
        try:
            self._library.delete_application(application["id"])
        except ApiClientError as error:
            self.error_label.setText(str(error))
        self.refresh()

    def submit(self):
        name, path = self.name_input.text().strip(), self.path_input.text().strip()
        if not name or not path:
            self.error_label.setText(
                "El nombre y la ruta del ejecutable son obligatorios."
            )
            return
        try:
            self._library.save_application(name, path, self._editing)
        except ApiClientError as error:
            self.error_label.setText(str(error))
            return
        self._editing = None
        self.error_label.clear()
        self.name_input.clear()
        self.path_input.clear()
        self.save_button.setText("Registrar aplicación")
        self.refresh()
