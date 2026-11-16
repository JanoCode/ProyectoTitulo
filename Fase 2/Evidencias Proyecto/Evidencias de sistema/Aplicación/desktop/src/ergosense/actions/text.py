from dataclasses import dataclass, field
from threading import Event


@dataclass(frozen=True)
class TextInput:
    text: str = ""
    key: str = ""
    cancelled: Event | None = field(default=None, compare=False, repr=False)
