from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from ..models import GameWindow


def character_key(name: str) -> str:
    return name.strip().casefold()


def character_names(value: object) -> list[str]:
    """Normalize persisted names without accepting strings as lists."""
    if not isinstance(value, (list, tuple)):
        return []
    result: list[str] = []
    seen: set[str] = set()
    for name in value:
        if not isinstance(name, str) or not name.strip():
            continue
        key = character_key(name)
        if key not in seen:
            result.append(name.strip())
            seen.add(key)
    return result


@dataclass
class CharacterRoster:
    """Names are scoped to the active profile/mode, never to a Windows handle.

    Rotation order may change; direct-access slots only change explicitly.
    Missing and ignored members keep their place until the user saves a new team.
    """

    order: list[str] = field(default_factory=list)
    slots: list[str] = field(default_factory=list)
    ignored: set[str] = field(default_factory=set)
    history: list[list[str]] = field(default_factory=list)

    def discover(self, windows: Mapping[int, GameWindow], preferred: Iterable[int] = ()) -> None:
        names = [windows[hwnd].pseudo for hwnd in preferred if hwnd in windows]
        names.extend(window.pseudo for window in windows.values())
        self.order = character_names([*self.order, *names])
        self.slots = character_names([*self.slots, *self.order])

    def resolve(self, name: str, windows: Mapping[int, GameWindow]) -> int | None:
        matches = [hwnd for hwnd, window in windows.items() if character_key(window.pseudo) == character_key(name)]
        # Two servers may use the same name: never silently choose one.
        return matches[0] if len(matches) == 1 else None

    def bindings(self, windows: Mapping[int, GameWindow]) -> list[int]:
        return [self.resolve(name, windows) or -(slot + 1) for slot, name in enumerate(self.slots)]

    def remember_order(self, windows: Mapping[int, GameWindow], managed: Iterable[int]) -> None:
        self.discover(windows, managed)
        counts = Counter(character_key(window.pseudo) for window in windows.values())
        names = [windows[hwnd].pseudo for hwnd in managed if hwnd in windows]
        names = [name for name in names if counts[character_key(name)] == 1]
        moving = {character_key(name) for name in names}
        pending = iter(names)
        # Leave offline/ignored names in place while permuting visible members.
        self.order = [next(pending) if character_key(name) in moving else name for name in self.order]

    def checkpoint(self) -> None:
        self.history.append(list(self.order))
        del self.history[:-20]

    def undo(self) -> bool:
        if not self.history:
            return False
        previous = self.history.pop()
        # Keep characters discovered after the saved operation.
        self.order = character_names([*previous, *self.order])
        return True
