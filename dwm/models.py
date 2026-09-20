from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GameWindow:
    hwnd: int
    title: str
    pseudo: str
    character_class: str = ""
    pid: int = field(default=0, compare=False)
    window_class: str = field(default="", compare=False)
    game_mode: str = field(default="", compare=False)
    process_image: str = field(default="", compare=False)

    @property
    def identity_fingerprint(self) -> tuple[int, str, str, str, str]:
        """Stable facts used to detect HWND reuse without affecting legacy equality."""
        return (
            int(self.pid or 0),
            str(self.window_class or ""),
            str(self.game_mode or ""),
            str(self.pseudo or "").strip().casefold(),
            str(self.process_image or "").strip().casefold(),
        )
