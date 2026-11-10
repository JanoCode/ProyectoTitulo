from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QDialog

from ergosense.api_client import ApiClientError
from ergosense.ui.macros_dialog import ApplicationsDialog, MacroEditor, MacrosDialog


@pytest.fixture
def library():
    result = Mock()
    result.macros = []
    result.applications = []
    result.device = "QA"
    result.trigger_problem.return_value = None
    return result


def fill(editor):
    editor.name_input.setText("Saludo")
    editor.triggers.itemAt(0).widget().editor.setText("escribir saludo")
    action = editor.actions.itemAt(0).widget()
    action.kind.setCurrentIndex(action.kind.findData("TYPE_TEXT"))
    action.editor.setText("Hola")


def test_editor_rejects_an_empty_name_without_writing(qapp, library):
    editor = MacroEditor(library)
    editor.submit()
    assert "obligatorio" in editor.error_label.text()
    library.save_macro.assert_not_called()
    editor.close()


def test_editor_saves_order_and_preserves_text_spaces(qapp, library):
    editor = MacroEditor(library)
    fill(editor)
    editor.add_action({"action_type": "TYPE_TEXT", "action_value": " segundo "})
    editor._move(editor.actions.itemAt(1).widget(), -1)
    editor.submit()
    data, identifier = library.save_macro.call_args.args
    assert identifier is None
    assert [step["action_value"] for step in data["actions"]] == [" segundo ", "Hola"]
    assert editor.result() == QDialog.DialogCode.Accepted
    editor.close()


def test_editor_keeps_changes_open_when_server_rejects(qapp, library):
    library.save_macro.side_effect = ApiClientError("Activador duplicado", 409)
    editor = MacroEditor(library)
    fill(editor)
    editor.submit()
    assert editor.result() != QDialog.DialogCode.Accepted
    assert editor.name_input.text() == "Saludo"
    assert editor.error_label.text() == "Activador duplicado"
    editor.close()


def test_application_registration_requires_both_fields(qapp, library):
    dialog = ApplicationsDialog(library)
    dialog.name_input.setText("Editor")
    dialog.submit()
    library.save_application.assert_not_called()
    assert "obligatorios" in dialog.error_label.text()
    dialog.close()


def test_application_editor_saves_the_selected_record(qapp, library):
    dialog = ApplicationsDialog(library)
    dialog.start_edit({"id": 4, "name": "Editor", "executable_path": r"C:\old.exe"})
    dialog.path_input.setText(r"C:\new.exe")
    dialog.submit()
    library.save_application.assert_called_once_with("Editor", r"C:\new.exe", 4)
    assert dialog._editing is None
    dialog.close()


def test_macro_switch_shows_server_failure(qapp, library):
    library.set_enabled.side_effect = ApiClientError("Sin conexión")
    dialog = MacrosDialog(library)
    dialog.set_enabled({"id": 1}, False)
    assert dialog.error_label.text() == "Sin conexión"
    dialog.close()
