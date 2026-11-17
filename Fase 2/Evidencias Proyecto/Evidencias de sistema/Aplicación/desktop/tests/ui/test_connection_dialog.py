from ergosense.api_client import ApiClientError
from ergosense.ui.connection_dialog import ConnectionDialog


class Client:
    base_url = "http://127.0.0.1:8000/api/v1"
    changed = False

    def check_server(self, url):
        raise ApiClientError("Servidor no disponible")

    def change_server(self, url):
        self.changed = True


def test_unreachable_server_does_not_replace_saved_connection(qapp, monkeypatch):
    saved = []
    monkeypatch.setattr("ergosense.ui.connection_dialog.save_server_url", saved.append)
    client = Client()
    dialog = ConnectionDialog(client)
    dialog.url_input.setText("https://example.org")
    dialog.submit()
    assert not client.changed
    assert saved == []
    assert dialog.error_label.text() == "Servidor no disponible"
    assert dialog.save_button.isEnabled()
