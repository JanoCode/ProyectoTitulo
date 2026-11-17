import json
import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

DEFAULT_API_URL = "http://127.0.0.1:8000/api/v1"


def configuration_path():
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData/Local")
    return base / "ErgoSense" / "connection.json"


def normalize_api_url(value):
    value = value.strip()
    try:
        url = urlsplit(value.strip())
        port = url.port
    except ValueError as error:
        raise ValueError("La dirección del servidor no es válida.") from error
    if (
        url.scheme not in ("http", "https")
        or not url.hostname
        or url.username is not None
        or url.password is not None
        or url.query
        or url.fragment
        or any(char.isspace() for char in value)
        or port == 0
    ):
        raise ValueError("Usa una dirección http:// o https:// sin credenciales.")
    path = url.path.rstrip("/") or "/api/v1"
    if not path.endswith("/api/v1"):
        raise ValueError("La dirección debe terminar en /api/v1.")
    return urlunsplit((url.scheme, url.netloc, path, "", ""))


def server_url():
    override = os.environ.get("ERGOSENSE_API_URL")
    if override:
        return normalize_api_url(override)
    try:
        data = json.loads(configuration_path().read_text(encoding="utf-8"))
        return normalize_api_url(data["api_url"])
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return DEFAULT_API_URL


def save_server_url(value):
    value = normalize_api_url(value)
    path = configuration_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"api_url": value}, indent=2), encoding="utf-8")
    temporary.replace(path)
