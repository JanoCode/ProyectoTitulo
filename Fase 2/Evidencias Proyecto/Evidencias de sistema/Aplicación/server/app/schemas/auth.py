"""Esquemas Pydantic para cuentas, configuración y tokens."""

import re
from datetime import datetime

from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def normalize_email(value: str) -> str:
    """Valida un correo y lo normaliza para evitar duplicados por mayúsculas."""
    try:
        result = validate_email(value.strip(), check_deliverability=False)
    except EmailNotValidError as error:
        raise ValueError("El correo electrónico no es válido.") from error
    return result.normalized.lower()


class RegisterRequest(BaseModel):
    """Datos necesarios para crear una cuenta."""

    name: str = Field(min_length=1, max_length=120)
    email: str
    password: str

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("El nombre es obligatorio.")
        return cleaned

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8 or not re.search(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]", value):
            raise ValueError(
                "La contraseña debe tener al menos 8 caracteres, letras y números."
            )
        if not re.search(r"\d", value):
            raise ValueError(
                "La contraseña debe tener al menos 8 caracteres, letras y números."
            )
        if len(value.encode("utf-8")) > 72:
            raise ValueError("La contraseña no puede superar 72 bytes.")
        return value


class LoginRequest(BaseModel):
    """Credenciales recibidas al iniciar sesión."""

    email: str
    password: str

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: str) -> str:
        return normalize_email(value)


class RefreshRequest(BaseModel):
    """Token persistente utilizado para solicitar acceso nuevo."""

    refresh_token: str = Field(min_length=1)


class UserResponse(BaseModel):
    """Información pública de una cuenta."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    created_at: datetime


class SettingResponse(BaseModel):
    """Preferencias que el desktop necesita para iniciar sus módulos."""

    model_config = ConfigDict(from_attributes=True)

    inactivity_break_minutes: int
    voice_enabled: bool
    gesture_enabled: bool


class SettingUpdateRequest(BaseModel):
    """Cambios de configuración: solo se modifican los campos enviados (PB-36 y PB-37).

    El período de aviso de 60 minutos no es configurable, por eso no aparece aquí.
    """

    # Un campo desconocido, por ejemplo uno para cambiar el aviso de 60 minutos, se
    # rechaza en vez de ignorarse en silencio (CP-03-15).
    model_config = ConfigDict(extra="forbid")

    # strict: solo números enteros, sin convertir textos como "10" ni decimales como
    # 2.5. gt=0: el tiempo de inactividad debe ser mayor que cero (CP-03-14). El valor
    # por defecto None indica "no se envió"; un null explícito se rechaza.
    inactivity_break_minutes: int = Field(default=None, gt=0, strict=True)
    voice_enabled: bool = Field(default=None, strict=True)
    gesture_enabled: bool = Field(default=None, strict=True)

    @model_validator(mode="after")
    def require_a_change(self):
        if not self.model_fields_set:
            raise ValueError("Debes indicar al menos un valor de configuración.")
        return self


class RegisterResponse(BaseModel):
    """Cuenta creada junto con su configuración inicial."""

    user: UserResponse
    settings: SettingResponse


class TokenPairResponse(BaseModel):
    """Resultado del login: identidad, preferencias y ambos tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_expires_in: int
    user: UserResponse
    settings: SettingResponse


class AccessTokenResponse(BaseModel):
    """Token de acceso renovado."""

    access_token: str
    token_type: str = "bearer"
    access_expires_in: int


class MessageResponse(BaseModel):
    """Respuesta breve para operaciones sin un recurso de salida."""

    message: str
