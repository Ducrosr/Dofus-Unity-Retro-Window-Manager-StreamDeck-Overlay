from __future__ import annotations

from ..models import GameWindow


def window_table_values(window: GameWindow, alias: str) -> tuple[str, str, str, str]:
    """Return independent Class, Name, Alias and HWND table values."""
    return (
        window.character_class or "—",
        window.pseudo or "—",
        alias or "—",
        str(window.hwnd),
    )
