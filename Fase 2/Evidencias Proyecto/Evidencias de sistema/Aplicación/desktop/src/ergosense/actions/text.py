from dataclasses import dataclass


@dataclass(frozen=True)
class TextInput:
    text: str = ""
    key: str = ""
