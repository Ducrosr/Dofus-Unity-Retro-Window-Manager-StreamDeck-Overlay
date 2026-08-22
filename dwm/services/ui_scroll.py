from __future__ import annotations


def wheel_scroll_units(delta: int) -> int:
    """Translate a Windows mouse-wheel delta into Tk vertical scroll units."""
    if not delta:
        return 0
    magnitude = max(1, abs(int(delta)) // 120)
    return -magnitude if delta > 0 else magnitude


def vertical_scroll_needed(first: float, last: float) -> bool:
    """Return whether a canvas viewport does not currently show all its content."""
    return first > 0.0 or last < 1.0
