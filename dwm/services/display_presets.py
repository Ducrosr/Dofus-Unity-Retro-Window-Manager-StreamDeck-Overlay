from __future__ import annotations

from typing import Mapping


DISPLAY_PRESET_IDS = ("minimal", "balanced", "complete")
DISPLAY_PRESET_LABELS = {
    "minimal": "Minimal",
    "balanced": "Équilibré",
    "complete": "Complet",
}

_MINIMAL_LAYOUT = {
    "left": "position",
    "line1": "name",
    "line2_left": "none",
    "line2_right": "none",
}
_FULL_LAYOUT = {
    "left": "position",
    "line1": "name",
    "line2_left": "class",
    "line2_right": "alias",
}

DISPLAY_PRESETS: Mapping[str, Mapping[str, object]] = {
    "minimal": {
        "rotation_overlay_auto_width": True,
        "rotation_overlay_show_title": False,
        "rotation_overlay_show_reorder_buttons": False,
        "rotation_overlay_layout": _MINIMAL_LAYOUT,
        "swap_notification_layout": _MINIMAL_LAYOUT,
        "show_popup_portraits": False,
        "show_popup_badges": False,
        "show_overlay_portraits": False,
        "show_overlay_badges": False,
    },
    "balanced": {
        "rotation_overlay_auto_width": True,
        "rotation_overlay_show_title": True,
        "rotation_overlay_show_reorder_buttons": False,
        "rotation_overlay_layout": _FULL_LAYOUT,
        "swap_notification_layout": _FULL_LAYOUT,
        "show_popup_portraits": True,
        "show_popup_badges": False,
        "show_overlay_portraits": True,
        "show_overlay_badges": False,
    },
    "complete": {
        "rotation_overlay_auto_width": True,
        "rotation_overlay_show_title": True,
        "rotation_overlay_show_reorder_buttons": True,
        "rotation_overlay_layout": _FULL_LAYOUT,
        "swap_notification_layout": _FULL_LAYOUT,
        "show_popup_portraits": True,
        "show_popup_badges": True,
        "show_overlay_portraits": True,
        "show_overlay_badges": True,
    },
}


def display_preset_values(preset_id: object) -> dict[str, object]:
    normalized = str(preset_id or "").strip().lower()
    if normalized not in DISPLAY_PRESETS:
        raise ValueError(f"Préréglage d’affichage inconnu : {preset_id}")
    values = dict(DISPLAY_PRESETS[normalized])
    values["rotation_overlay_layout"] = dict(values["rotation_overlay_layout"])
    values["swap_notification_layout"] = dict(values["swap_notification_layout"])
    return values


def apply_display_preset(settings: object, preset_id: object) -> None:
    for key, value in display_preset_values(preset_id).items():
        setattr(settings, key, value)

