from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping

from ..models import GameWindow
from .character_visuals import bundled_icon_data_uri


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


def retain_character_slots(
    entries: list[dict[str, object]],
    names: list[str],
    bindings: list[int],
    aliases: Mapping[str, str],
    visuals: Mapping[str, Mapping[str, str]],
) -> list[dict[str, object]]:
    """Keep offline slots visible; their negative handles cannot activate a window."""
    by_hwnd = {entry["hwnd"]: entry for entry in entries}
    result: list[dict[str, object]] = []
    for slot, (name, hwnd) in enumerate(zip(names, bindings, strict=True), 1):
        if hwnd in by_hwnd:
            result.append({**by_hwnd[hwnd], "slot": slot, "available": True})
        else:
            appearance = visuals.get(name, {})
            badge = str(appearance.get("badge") or "none")
            result.append({
                "slot": slot, "hwnd": -slot, "position": None,
                "pseudo": name, "name": name, "alias": aliases.get(name, ""),
                "title": "", "character_class": "", "available": False,
                "active": False, "ignored": False, "attention": False,
                "portrait": str(appearance.get("portrait") or ""),
                "badge": badge, "badge_image": bundled_icon_data_uri(badge),
            })
    return result


def build_streamdeck_windows(
    windows: Mapping[int, GameWindow],
    streamdeck_order: Iterable[int],
    managed_order: Iterable[int],
    ignored: set[int],
    aliases: Mapping[str, str],
    active_hwnd: int | None,
    attention_hwnds: Collection[int] = (),
    character_visuals: Mapping[str, Mapping[str, str]] | None = None,
) -> list[dict[str, object]]:
    """Build the public window list without dropping ignored characters."""
    managed_positions = {hwnd: position for position, hwnd in enumerate(managed_order, start=1)}
    attention_positions = {
        int(hwnd): position
        for position, hwnd in enumerate(dict.fromkeys(attention_hwnds), start=1)
    }
    result: list[dict[str, object]] = []

    for slot, hwnd in enumerate(streamdeck_order, start=1):
        window = windows.get(hwnd)
        if window is None:
            continue
        alias = (aliases.get(window.pseudo) or "").strip()
        appearance = (character_visuals or {}).get(window.pseudo, {})
        badge = str(appearance.get("badge") or "none")
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
                "attention": hwnd in attention_positions,
                "attention_order": attention_positions.get(hwnd),
                "portrait": str(appearance.get("portrait") or ""),
                "badge": badge,
                "badge_image": bundled_icon_data_uri(badge),
            }
        )
    return result
