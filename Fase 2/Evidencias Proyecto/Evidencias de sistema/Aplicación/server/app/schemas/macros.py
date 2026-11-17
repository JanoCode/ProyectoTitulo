"""Esquemas de macros, activadores, acciones y aplicaciones (PB-38 a PB-41)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core import catalog

TriggerType = Literal["VOICE", "GESTURE"]
ActionType = Literal["OPEN_URL", "OPEN_APP", "KEY_PRESS", "TYPE_TEXT", "MOUSE_CLICK"]


def required_text(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("El campo es obligatorio.")
    return cleaned


class TriggerData(BaseModel):
    """Frase de voz o gesto que ejecuta la macro (PB-39)."""

    model_config = ConfigDict(extra="forbid")

    trigger_type: TriggerType
    trigger_value: str = Field(min_length=1, max_length=catalog.MAX_PHRASE_LENGTH)


class ActionData(BaseModel):
    """Acción de la macro; su orden es su posición en la lista (PB-40)."""

    model_config = ConfigDict(extra="forbid")

    action_type: ActionType
    action_value: str = Field(min_length=1, max_length=catalog.MAX_TEXT_LENGTH)

    @model_validator(mode="after")
    def check_value(self):
        error = catalog.action_error(self.action_type, self.action_value)
        if error:
            raise ValueError(error)
        return self


class MacroData(BaseModel):
    """Macro completa: se usa para crearla y para reemplazarla al editarla."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    enabled: bool = Field(default=True, strict=True)  # nueva macro: activada (PB-38)
    triggers: list[TriggerData] = Field(min_length=1, max_length=10)
    actions: list[ActionData] = Field(min_length=1, max_length=20)

    _clean_name = field_validator("name")(required_text)

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str | None) -> str | None:
        return (value or "").strip() or None


class MacroStateUpdate(BaseModel):
    """Activa o desactiva una macro sin modificarla (PB-43)."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(strict=True)


class TriggerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trigger_type: str
    trigger_value: str


class ActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action_type: str
    action_value: str
    execution_order: int


class MacroResponse(BaseModel):
    """Macro con sus activadores y sus acciones, ordenadas por execution_order."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    enabled: bool
    triggers: list[TriggerResponse]
    actions: list[ActionResponse]


class ApplicationData(BaseModel):
    """Aplicación registrada en un computador (PB-41)."""

    model_config = ConfigDict(extra="forbid")

    device_name: str = Field(min_length=1, max_length=255)
    name: str = Field(min_length=1, max_length=255)
    executable_path: str = Field(min_length=1, max_length=1000)

    _clean = field_validator("device_name", "name", "executable_path")(required_text)


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_name: str
    name: str
    executable_path: str
