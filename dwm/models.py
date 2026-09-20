from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GameWindow:
    hwnd: int
    title: str
    pseudo: str
    character_class: str = ""
    process_id: int = 0
    window_class: str = ""
    game_mode: str = ""
    process_image: str = ""
