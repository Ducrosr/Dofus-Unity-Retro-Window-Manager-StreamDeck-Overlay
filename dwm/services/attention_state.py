from __future__ import annotations

from collections.abc import Collection


class WindowAttentionState:
    """Track game windows waiting for the user until they receive focus."""

    def __init__(self) -> None:
        self._pending: set[int] = set()

    def mark(self, hwnd: int, known_hwnds: Collection[int], active_hwnd: int | None = None) -> bool:
        hwnd = int(hwnd)
        if hwnd <= 0 or hwnd not in known_hwnds or hwnd == active_hwnd:
            return False
        before = len(self._pending)
        self._pending.add(hwnd)
        return len(self._pending) != before

    def clear(self, hwnd: int) -> bool:
        hwnd = int(hwnd)
        if hwnd not in self._pending:
            return False
        self._pending.remove(hwnd)
        return True

    def discard_unknown(self, known_hwnds: Collection[int]) -> bool:
        known = {int(hwnd) for hwnd in known_hwnds}
        updated = self._pending.intersection(known)
        if updated == self._pending:
            return False
        self._pending = updated
        return True

    def reset(self) -> bool:
        if not self._pending:
            return False
        self._pending.clear()
        return True

    def snapshot(self) -> set[int]:
        return set(self._pending)
