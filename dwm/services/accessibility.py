from __future__ import annotations

from collections.abc import Mapping


def clamp_ui_scale_percent(value: object) -> int:
    try:
        scale = int(value)
    except (TypeError, ValueError):
        scale = 100
    return max(80, min(160, scale))


def high_contrast_palette(
    palette: Mapping[str, str],
    *,
    enabled: bool,
) -> dict[str, str]:
    result = dict(palette)
    if not enabled:
        return result
    result.update(
        {
            "bg": "#000000",
            "bg2": "#101010",
            "bg3": "#202020",
            "fg": "#ffffff",
            "muted": "#e5e7eb",
            "line": "#ffffff",
            "header": "#ffffff",
            "button_hover": "#3a3a3a",
            "on_dark": "#ffffff",
        }
    )
    return result


def motion_allowed(*, reduce_motion: bool) -> bool:
    return not bool(reduce_motion)

