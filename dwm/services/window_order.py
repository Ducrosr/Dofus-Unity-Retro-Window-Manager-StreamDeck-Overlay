from __future__ import annotations

from collections.abc import Iterable


def move_column(order: Iterable[str], source: str, target: str) -> list[str]:
    """Move one displayed column immediately before another."""
    result = list(order)
    if source == target or source not in result or target not in result:
        return result
    result.remove(source)
    result.insert(result.index(target), source)
    return result


def move_window(order: Iterable[int], hwnd: int, target_hwnd: int, *, after: bool = False) -> list[int]:
    """Move one hwnd before or after another while preserving every other item."""
    result = list(order)
    if hwnd == target_hwnd or hwnd not in result or target_hwnd not in result:
        return result

    result.remove(hwnd)
    target_index = result.index(target_hwnd)
    result.insert(target_index + (1 if after else 0), hwnd)
    return result


def move_window_by_delta(order: Iterable[int], hwnd: int, delta: int) -> list[int]:
    """Move one hwnd by one or more positions without wrapping at the edges."""
    result = list(order)
    if hwnd not in result or delta == 0:
        return result
    index = result.index(hwnd)
    new_index = index + int(delta)
    if not 0 <= new_index < len(result):
        return result
    result.pop(index)
    result.insert(new_index, hwnd)
    return result


def align_streamdeck_slots_with_managed(
    streamdeck_order: Iterable[int], managed_order: Iterable[int], ignored: set[int]
) -> list[int]:
    """Reorder managed slots while leaving ignored characters anchored in place."""
    current = list(dict.fromkeys(streamdeck_order))
    managed = list(dict.fromkeys(managed_order))
    managed_set = set(managed)
    managed_iter = iter(managed)
    result: list[int] = []

    for hwnd in current:
        if hwnd in ignored:
            result.append(hwnd)
        elif hwnd in managed_set:
            result.append(next(managed_iter))
        else:
            result.append(hwnd)

    for hwnd in managed_iter:
        if hwnd not in result:
            result.append(hwnd)
    return result
