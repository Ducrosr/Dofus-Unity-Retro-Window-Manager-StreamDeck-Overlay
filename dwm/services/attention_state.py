from __future__ import annotations

from collections.abc import Collection


class WindowAttentionState:
    """Track game windows waiting for the user until they receive focus."""

    def __init__(self) -> None:
        self._pending: list[int] = []

    def mark(self, hwnd: int, known_hwnds: Collection[int], active_hwnd: int | None = None) -> bool:
        hwnd = int(hwnd)
        if hwnd <= 0 or hwnd not in known_hwnds or hwnd == active_hwnd:
            return False
        if hwnd in self._pending:
            return False
        self._pending.append(hwnd)
        return True

    def clear(self, hwnd: int) -> bool:
        hwnd = int(hwnd)
        if hwnd not in self._pending:
            return False
        self._pending.remove(hwnd)
        return True

    def discard_unknown(self, known_hwnds: Collection[int]) -> bool:
        known = {int(hwnd) for hwnd in known_hwnds}
        updated = [hwnd for hwnd in self._pending if hwnd in known]
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

    def queue(self) -> tuple[int, ...]:
        """Return pending windows from the oldest request to the newest."""
        return tuple(self._pending)

    def next(self) -> int | None:
        """Return the oldest pending window without clearing it."""
        return self._pending[0] if self._pending else None

    def rank(self, hwnd: int) -> int | None:
        """Return the one-based position of a window in the pending queue."""
        try:
            return self._pending.index(int(hwnd)) + 1
        except ValueError:
            return None
