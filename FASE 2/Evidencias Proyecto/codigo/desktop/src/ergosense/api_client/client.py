"""Comunicación HTTP, renovación automática y manejo de errores en español."""

from datetime import datetime

import httpx

from ergosense.api_client.token_store import KeyringTokenStore


class ApiClientError(Exception):
    """Error apto para mostrar en la interfaz sin detalles internos."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class ApiClient:
    """Único punto del desktop que conoce rutas, tokens y solicitudes HTTP."""

    def __init__(
        self,
        base_url: str,
        *,
        token_store=None,
        http_client: httpx.Client | None = None,
        timeout_seconds: float = 5.0,
    ):
        self._base_url = base_url.rstrip("/")
        self._token_store = token_store or KeyringTokenStore()
        self._http = http_client or httpx.Client(timeout=timeout_seconds)
        self._owns_http_client = http_client is None
        self._access_token = None
        self.user = None
        self.settings = None

    def register(self, name: str, email: str, password: str) -> dict:
        """Crea una cuenta; el login continúa siendo una acción separada."""
        return self._request(
            "POST",
            "/auth/register",
            json={"name": name, "email": email, "password": password},
            authenticated=False,
        )

    def login(self, email: str, password: str) -> dict:
        """Inicia sesión y guarda solo el refresh token de forma persistente."""
        data = self._request(
            "POST",
            "/auth/login",
            json={"email": email, "password": password},
            authenticated=False,
        )
        self._accept_login(data)
        return data

    def restore_session(self) -> bool:
        """Recupera la sesión sin contraseña mediante el token protegido."""
        if not self._token_store.get():
            return False
        try:
            self._refresh_access()
            self.user = self._request("GET", "/users/me")
            self.settings = self._request("GET", "/settings")
        except ApiClientError as error:
            # Un 401 confirma que el token dejó de servir. Un fallo de red no:
            # en ese caso se conserva para volver a intentar en el próximo inicio.
            if error.status_code is not None:
                self.clear_local_session()
            else:
                self._access_token = None
                self.user = None
                self.settings = None
            return False
        return True

    def logout(self) -> None:
        """Revoca en el servidor y siempre elimina las credenciales locales."""
        refresh_token = self._token_store.get()
        try:
            if refresh_token and self._access_token:
                self._request(
                    "POST",
                    "/auth/logout",
                    json={"refresh_token": refresh_token},
                    retry_refresh=False,
                )
        finally:
            self.clear_local_session()

    def get_settings(self) -> dict:
        self.settings = self._request("GET", "/settings")
        return self.settings

    def update_settings(self, changes: dict) -> dict:
        """Guarda en el servidor los cambios de configuración (PB-36 y PB-37)."""
        self.settings = self._request("PATCH", "/settings", json=changes)
        return self.settings

    def start_usage_session(self, started_at: datetime) -> dict:
        return self._request(
            "POST",
            "/usage-sessions",
            json={"started_at": started_at.isoformat()},
        )

    def end_usage_session(self, session_id: int, ended_at: datetime) -> dict:
        return self._request(
            "PATCH",
            f"/usage-sessions/{session_id}",
            json={"ended_at": ended_at.isoformat()},
        )

    def start_break(
        self,
        session_id: int,
        started_at: datetime,
    ) -> dict:
        return self._request(
            "POST",
            f"/usage-sessions/{session_id}/breaks",
            json={"started_at": started_at.isoformat()},
        )

    def end_break(self, break_id: int, ended_at: datetime) -> dict:
        return self._request(
            "PATCH",
            f"/breaks/{break_id}",
            json={"ended_at": ended_at.isoformat()},
        )

    def clear_local_session(self) -> None:
        """La contraseña nunca se guarda; aquí se quitan tokens y datos cargados."""
        self._token_store.clear()
        self._access_token = None
        self.user = None
        self.settings = None

    def close(self) -> None:
        if self._owns_http_client:
            self._http.close()

    def _accept_login(self, data: dict) -> None:
        self._access_token = data["access_token"]
        self._token_store.save(data["refresh_token"])
        self.user = data["user"]
        self.settings = data["settings"]

    def _refresh_access(self) -> None:
        refresh_token = self._token_store.get()
        if not refresh_token:
            raise ApiClientError("No existe una sesión guardada.", 401)
        data = self._request(
            "POST",
            "/auth/refresh",
            json={"refresh_token": refresh_token},
            authenticated=False,
            retry_refresh=False,
        )
        self._access_token = data["access_token"]

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        authenticated: bool = True,
        retry_refresh: bool = True,
    ) -> dict:
        headers = {}
        if authenticated:
            if not self._access_token:
                raise ApiClientError("Debes iniciar sesión.", 401)
            headers["Authorization"] = f"Bearer {self._access_token}"

        try:
            response = self._http.request(
                method,
                f"{self._base_url}{path}",
                json=json,
                headers=headers,
            )
        except httpx.RequestError as error:
            raise ApiClientError(
                "No fue posible conectar con el servidor de ErgoSense."
            ) from error

        if response.status_code == 401 and authenticated and retry_refresh:
            self._refresh_access()
            return self._request(
                method,
                path,
                json=json,
                authenticated=True,
                retry_refresh=False,
            )
        if response.is_error:
            try:
                detail = response.json().get("detail")
            except ValueError:
                detail = None
            raise ApiClientError(
                detail or "El servidor no pudo completar la operación.",
                response.status_code,
            )
        if not response.content:
            return {}
        return response.json()
