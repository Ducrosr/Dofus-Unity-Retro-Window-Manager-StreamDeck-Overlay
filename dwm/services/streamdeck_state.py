from __future__ import annotations

from collections.abc import Iterable, Mapping

from ..models import GameWindow


def reconcile_streamdeck_order(
    current_order: Iterable[int],
    windows: Mapping[int, GameWindow],
    preferred_order: Iterable[int] = (),
) -> list[int]:
    """Keep Stream Deck slots stable while adding/removing detected windows."""
    result: list[int] = []
    seen: set[int] = set()

    for hwnd in (*current_order, *preferred_order, *windows.keys()):
        if hwnd in windows and hwnd not in seen:
            result.append(hwnd)
            seen.add(hwnd)
    return result


def build_streamdeck_windows(
    windows: Mapping[int, GameWindow],
    streamdeck_order: Iterable[int],
    managed_order: Iterable[int],
    ignored: set[int],
    aliases: Mapping[str, str],
    active_hwnd: int | None,
) -> list[dict[str, object]]:
    """Build the public window list without dropping ignored characters."""
    managed_positions = {hwnd: position for position, hwnd in enumerate(managed_order, start=1)}
    result: list[dict[str, object]] = []

    for slot, hwnd in enumerate(streamdeck_order, start=1):
        window = windows.get(hwnd)
        if window is None:
            continue
        alias = (aliases.get(window.pseudo) or "").strip()
        result.append(
            {
                "slot": slot,
                "position": managed_positions.get(hwnd),
                "hwnd": hwnd,
                "pseudo": window.pseudo,
                "alias": alias,
                # Keep name and alias strictly separate. In particular, clearing
                # an alias must immediately publish an empty alias instead of
                # leaving a stale display name in Stream Deck.
                "name": window.pseudo,
                "character_class": window.character_class,
                "title": window.title,
                "active": hwnd == active_hwnd,
                "ignored": hwnd in ignored,
            }
        )
    return result
