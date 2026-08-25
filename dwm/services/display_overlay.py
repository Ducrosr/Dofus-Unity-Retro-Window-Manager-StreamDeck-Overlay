from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Collection, Mapping, Sequence

from ..models import GameWindow


OVERLAY_ANCHORS = (
    "top_left",
    "top_center",
    "top_right",
    "bottom_left",
    "bottom_center",
    "bottom_right",
)

OVERLAY_ORIENTATIONS = ("vertical", "horizontal")

OVERLAY_LAYOUT_SLOTS = ("left", "line1", "line2_left", "line2_right")
OVERLAY_FIELDS = ("none", "position", "name", "class", "alias")
DEFAULT_ROTATION_OVERLAY_LAYOUT = {
    "left": "position",
    "line1": "name",
    "line2_left": "class",
    "line2_right": "alias",
}

_TK_GEOMETRY_PATTERN = re.compile(
    r"^(?P<width>\d+)x(?P<height>\d+)(?P<x>[+-]\d+)(?P<y>[+-]\d+)$"
)


@dataclass(frozen=True)
class CharacterDisplay:
    hwnd: int
    pseudo: str
    character_class: str
    alias: str
    position: int | None
    total: int
    active: bool
    attention: bool = False
    attention_order: int | None = None
    portrait_data: str = ""
    badge: str = "none"

    @property
    def primary_text(self) -> str:
        return self.alias or self.pseudo

    @property
    def secondary_text(self) -> str:
        parts: list[str] = []
        if self.alias and self.pseudo:
            parts.append(self.pseudo)
        if self.character_class:
            parts.append(self.character_class)
        return " · ".join(parts)

    @property
    def position_text(self) -> str:
        if self.position is None:
            return "Hors rotation"
        return f"{self.position} / {self.total}"


def normalize_overlay_layout(value: object) -> dict[str, str]:
    """Return a complete, safe layout for the persistent rotation overlay."""
    raw = value if isinstance(value, Mapping) else {}
    result: dict[str, str] = {}
    for slot in OVERLAY_LAYOUT_SLOTS:
        requested = str(raw.get(slot, "") or "").strip().lower()
        result[slot] = (
            requested
            if requested in OVERLAY_FIELDS
            else DEFAULT_ROTATION_OVERLAY_LAYOUT[slot]
        )
    return result


def normalize_overlay_orientation(value: object) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in OVERLAY_ORIENTATIONS else "vertical"


def overlay_field_text(entry: CharacterDisplay, field: str) -> str:
    """Resolve one user-selectable overlay field to its visible text."""
    normalized = str(field or "").strip().lower()
    if normalized == "position":
        return str(entry.position) if entry.position is not None else "—"
    if normalized == "name":
        return entry.pseudo or "—"
    if normalized == "class":
        return entry.character_class or "—"
    if normalized == "alias":
        return entry.alias or "—"
    return ""


def compose_overlay_row(
    entry: CharacterDisplay,
    layout: object,
) -> tuple[str, str, str]:
    """Build the left marker and the two right-hand text lines."""
    normalized = normalize_overlay_layout(layout)
    left = overlay_field_text(entry, normalized["left"])
    line1 = overlay_field_text(entry, normalized["line1"])
    line2_parts = [
        overlay_field_text(entry, normalized["line2_left"]),
        overlay_field_text(entry, normalized["line2_right"]),
    ]
    line2 = " · ".join(part for part in line2_parts if part)
    return left, line1, line2


def build_rotation_displays(
    windows: Mapping[int, GameWindow],
    managed_order: Sequence[int],
    aliases: Mapping[str, str],
    active_hwnd: int | None,
    attention_hwnds: Collection[int] = (),
    character_visuals: Mapping[str, Mapping[str, str]] | None = None,
) -> list[CharacterDisplay]:
    attention_order = {
        int(hwnd): position
        for position, hwnd in enumerate(dict.fromkeys(attention_hwnds), start=1)
    }
    total = sum(1 for hwnd in managed_order if hwnd in windows)
    result: list[CharacterDisplay] = []
    position = 0
    for hwnd in managed_order:
        window = windows.get(hwnd)
        if window is None:
            continue
        position += 1
        appearance = (character_visuals or {}).get(window.pseudo, {})
        result.append(
            CharacterDisplay(
                hwnd=hwnd,
                pseudo=window.pseudo,
                character_class=window.character_class or "",
                alias=(aliases.get(window.pseudo) or "").strip(),
                position=position,
                total=total,
                active=hwnd == active_hwnd,
                attention=hwnd in attention_order,
                attention_order=attention_order.get(hwnd),
                portrait_data=str(appearance.get("portrait") or ""),
                badge=str(appearance.get("badge") or "none"),
            )
        )
    return result


def build_single_display(
    window: GameWindow,
    *,
    aliases: Mapping[str, str],
    managed_order: Sequence[int],
    active: bool,
    attention: bool = False,
    attention_order: int | None = None,
    appearance: Mapping[str, str] | None = None,
) -> CharacterDisplay:
    try:
        position = list(managed_order).index(window.hwnd) + 1
    except ValueError:
        position = None
    total = len(managed_order)
    return CharacterDisplay(
        hwnd=window.hwnd,
        pseudo=window.pseudo,
        character_class=window.character_class or "",
        alias=(aliases.get(window.pseudo) or "").strip(),
        position=position,
        total=total,
        active=active,
        attention=bool(attention),
        attention_order=(int(attention_order) if attention and attention_order else None),
        portrait_data=str((appearance or {}).get("portrait") or ""),
        badge=str((appearance or {}).get("badge") or "none"),
    )


def normalize_overlay_anchor(value: str) -> str:
    normalized = (value or "").strip().lower()
    return normalized if normalized in OVERLAY_ANCHORS else "top_center"


def clamp_overlay_opacity(value: object) -> int:
    try:
        opacity = int(value)
    except (TypeError, ValueError):
        opacity = 88
    return max(35, min(100, opacity))


def clamp_notification_duration(value: object) -> int:
    try:
        duration = int(value)
    except (TypeError, ValueError):
        duration = 1400
    return max(600, min(5000, duration))


def calculate_overlay_text_scale(
    width: object,
    height: object,
    row_count: object,
    *,
    locked: bool,
    fixed_height: bool,
    show_title: bool = True,
) -> float:
    """Scale overlay text with both the available width and per-row height."""
    try:
        safe_width = max(1, int(width))
        safe_height = max(1, int(height))
        safe_rows = max(0, int(row_count))
    except (TypeError, ValueError):
        safe_width, safe_height, safe_rows = 300, 46, 0

    width_scale = safe_width / 300
    if not fixed_height or safe_rows == 0:
        return max(0.55, min(2.2, width_scale))

    header_height = 4 if locked or not show_title else 24
    row_height = max(1.0, (safe_height - header_height) / safe_rows)
    height_scale = row_height / 46
    return max(0.55, min(2.2, width_scale, height_scale))


def place_inside_rect(
    target_rect: tuple[int, int, int, int],
    overlay_size: tuple[int, int],
    anchor: str,
    *,
    margin: int = 28,
) -> tuple[int, int]:
    left, top, right, bottom = target_rect
    width, height = overlay_size
    anchor = normalize_overlay_anchor(anchor)

    if anchor.endswith("left"):
        x = left + margin
    elif anchor.endswith("right"):
        x = right - width - margin
    else:
        x = left + ((right - left) - width) // 2

    if anchor.startswith("bottom"):
        y = bottom - height - margin
    else:
        y = top + margin

    max_x = max(left, right - width)
    max_y = max(top, bottom - height)
    return max(left, min(x, max_x)), max(top, min(y, max_y))


def parse_tk_geometry(value: object) -> tuple[int, int, int, int] | None:
    """Parse a complete Tk geometry string into width, height, x and y."""
    match = _TK_GEOMETRY_PATTERN.fullmatch(str(value or "").strip())
    if match is None:
        return None
    width = int(match.group("width"))
    height = int(match.group("height"))
    if width <= 0 or height <= 0:
        return None
    return width, height, int(match.group("x")), int(match.group("y"))


def recover_window_position(
    width: object,
    height: object,
    x: object,
    y: object,
    display_rects: Sequence[tuple[int, int, int, int]],
    *,
    min_visible_width: int = 64,
    min_visible_height: int = 32,
) -> tuple[int, int]:
    """Keep a saved position when visible, otherwise center it on the nearest display."""
    try:
        safe_width = max(1, int(width))
        safe_height = max(1, int(height))
        safe_x = int(x)
        safe_y = int(y)
    except (TypeError, ValueError):
        safe_width, safe_height, safe_x, safe_y = 300, 80, 0, 0

    valid_displays = [
        (int(left), int(top), int(right), int(bottom))
        for left, top, right, bottom in display_rects
        if int(right) > int(left) and int(bottom) > int(top)
    ]
    if not valid_displays:
        return safe_x, safe_y

    required_width = min(safe_width, max(1, int(min_visible_width)))
    required_height = min(safe_height, max(1, int(min_visible_height)))
    for left, top, right, bottom in valid_displays:
        visible_width = max(0, min(safe_x + safe_width, right) - max(safe_x, left))
        visible_height = max(0, min(safe_y + safe_height, bottom) - max(safe_y, top))
        if visible_width >= required_width and visible_height >= required_height:
            return safe_x, safe_y

    center_x = safe_x + safe_width / 2
    center_y = safe_y + safe_height / 2

    def distance_to_display(rect: tuple[int, int, int, int]) -> float:
        left, top, right, bottom = rect
        nearest_x = max(left, min(center_x, right))
        nearest_y = max(top, min(center_y, bottom))
        return (center_x - nearest_x) ** 2 + (center_y - nearest_y) ** 2

    left, top, right, bottom = min(valid_displays, key=distance_to_display)
    display_width = right - left
    display_height = bottom - top
    recovered_x = left if safe_width >= display_width else left + (display_width - safe_width) // 2
    recovered_y = top if safe_height >= display_height else top + (display_height - safe_height) // 2
    return recovered_x, recovered_y


def format_tk_geometry(width: int, height: int, x: int, y: int) -> str:
    return f"{int(width)}x{int(height)}{int(x):+d}{int(y):+d}"
