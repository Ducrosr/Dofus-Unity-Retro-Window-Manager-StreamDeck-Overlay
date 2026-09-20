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
    def identity_fingerprint(self) -> tuple[int, str, str, str, str]:
        """Stable-enough identity used to detect a reused HWND before focus."""
        return (
            int(self.pid or 0),
            str(self.window_class or "").casefold(),
            str(self.game_mode or "").casefold(),
            str(self.pseudo or "").strip().casefold(),
            str(self.process_path or "").strip().casefold(),
        )
