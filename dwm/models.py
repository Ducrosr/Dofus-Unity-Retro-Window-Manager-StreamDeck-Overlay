from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GameWindow:
    hwnd: int
    title: str
    pseudo: str
    character_class: str = ""
    pid: int = 0
    window_class: str = ""
    game_mode: str = ""
    process_path: str = ""

    @property
    def identity(self) -> tuple[int, str, str, str, str]:
        """Stable-enough fingerprint used to revalidate a HWND before mutation."""
        return (
            int(self.pid or 0),
            str(self.window_class or ""),
            str(self.game_mode or ""),
            str(self.pseudo or "").casefold(),
            str(self.process_path or "").casefold(),
        )
