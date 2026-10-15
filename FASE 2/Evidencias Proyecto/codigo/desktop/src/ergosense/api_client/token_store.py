"""Almacenamiento protegido del token de renovación en Windows."""

from typing import Protocol

import keyring

SERVICE_NAME = "ErgoSense"
TOKEN_NAME = "refresh-token"


class TokenStore(Protocol):
    """Contrato pequeño que permite reemplazar keyring durante las pruebas."""

    def get(self) -> str | None: ...

    def save(self, token: str) -> None: ...

    def clear(self) -> None: ...


class KeyringTokenStore:
    """Usa el Administrador de credenciales, no un archivo del proyecto."""

    def get(self) -> str | None:
        return keyring.get_password(SERVICE_NAME, TOKEN_NAME)

    def save(self, token: str) -> None:
        keyring.set_password(SERVICE_NAME, TOKEN_NAME, token)

    def clear(self) -> None:
        try:
            keyring.delete_password(SERVICE_NAME, TOKEN_NAME)
        except keyring.errors.PasswordDeleteError:
            # Borrar un token inexistente también deja el estado correcto.
            pass
