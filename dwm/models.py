from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GameWindow:
    hwnd: int
    title: str
    pseudo: str
    character_class: str = ""
