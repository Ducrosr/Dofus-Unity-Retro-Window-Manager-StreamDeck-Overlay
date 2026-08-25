from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable


_MODIFIER_KEYSYMS = {
    "Control_L",
    "Control_R",
    "Alt_L",
    "Alt_R",
    "Shift_L",
    "Shift_R",
    "Meta_L",
    "Meta_R",
    "Super_L",
    "Super_R",
    "Win_L",
    "Win_R",
}
_SPECIAL_KEYSYMS = {
    "Return": "Enter",
    "Escape": "Esc",
    "space": "Space",
    "BackSpace": "Backspace",
    "Delete": "Delete",
    "Home": "Home",
    "End": "End",
    "Prior": "PageUp",
    "Next": "PageDown",
    "Left": "Left",
    "Up": "Up",
    "Right": "Right",
    "Down": "Down",
    "Tab": "Tab",
}


def captured_hotkey_spec(keysym: object, state: object) -> str | None:
    key_name = str(keysym or "").strip()
    if not key_name or key_name in _MODIFIER_KEYSYMS:
        return None

    if re.fullmatch(r"F(?:[1-9]|1\d|2[0-4])", key_name, flags=re.IGNORECASE):
        key = key_name.upper()
    elif len(key_name) == 1 and key_name.isascii() and key_name.isalnum():
        key = key_name.upper()
    else:
        key = _SPECIAL_KEYSYMS.get(key_name)
    if key is None:
        return None

    try:
        mask = int(state)
    except (TypeError, ValueError):
        mask = 0
    modifiers: list[str] = []
    if mask & 0x0004:
        modifiers.append("Ctrl")
    if mask & 0x0008:
        modifiers.append("Alt")
    if mask & 0x0001:
        modifiers.append("Shift")
    if mask & 0x0040:
        modifiers.append("Win")
    return "+".join((*modifiers, key))


@dataclass(frozen=True)
class HotkeyConflict:
    spec: str
    labels: tuple[str, ...]


def find_hotkey_conflicts(
    assignments: Iterable[tuple[str, str]],
    parser: Callable[[str], object],
) -> list[HotkeyConflict]:
    grouped: dict[object, list[tuple[str, str]]] = {}
    for label, raw_spec in assignments:
        spec = str(raw_spec or "").strip()
        if not spec:
            continue
        parsed = parser(spec)
        grouped.setdefault(parsed, []).append((label, spec))

    conflicts = [
        HotkeyConflict(spec=items[0][1], labels=tuple(label for label, _spec in items))
        for items in grouped.values()
        if len(items) > 1
    ]
    return sorted(conflicts, key=lambda conflict: conflict.spec.casefold())


def describe_registration_errors(
    errors: Iterable[str],
    labels_by_id: dict[int, str],
) -> str:
    descriptions: list[str] = []
    for error in errors:
        match = re.search(r"\bid=(\d+)\b", str(error))
        hotkey_id = int(match.group(1)) if match else -1
        label = labels_by_id.get(hotkey_id, f"ID {hotkey_id}" if hotkey_id >= 0 else "Raccourci")
        descriptions.append(f"• {label} : combinaison refusée ou déjà utilisée par Windows")
    return "\n".join(dict.fromkeys(descriptions))

