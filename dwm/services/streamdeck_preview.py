from __future__ import annotations


STREAMDECK_PROFILE_LAYOUTS: dict[str, tuple[tuple[str | int | None, ...], ...]] = {
    "standard": (
        ("move-up", 1, 2, 3, 4),
        ("move-down", 5, 6, 7, 8),
        ("show", "toggle-ignore", "refresh", "previous", "next"),
    ),
    "mini": ((1, 2, 3), (4, "previous", "next")),
    "xl": (
        (1, 2, 3, 4, 5, 6, 7, 8),
        (
            "move-up",
            "move-down",
            "show",
            "toggle-ignore",
            "refresh",
            "previous",
            "next",
            "next-attention",
        ),
        (None, None, None, None, None, None, None, None),
        (None, None, None, None, None, None, None, None),
    ),
    "plus": ((1, 2, 3, 4), (5, 6, "previous", "next")),
    "neo": ((1, 2, 3, 4), (5, 6, "previous", "next")),
}

STREAMDECK_PROFILE_LABELS = {
    "standard": "Stream Deck · 15 touches",
    "mini": "Stream Deck Mini · 6 touches",
    "xl": "Stream Deck XL · 32 touches",
    "plus": "Stream Deck + · 8 touches",
    "neo": "Stream Deck Neo · 8 touches",
}

# Backward-compatible name used by existing consumers and tests.
STREAMDECK_PROFILE_LAYOUT = STREAMDECK_PROFILE_LAYOUTS["standard"]

STREAMDECK_ACTION_LABELS = {
    "move-up": "☰  ↑\nMonter",
    "move-down": "☰  ↓\nDescendre",
    "show": "DWM\nAfficher",
    "toggle-ignore": "⊘\nIgnorer",
    "refresh": "↻\nActualiser",
    "previous": "←\nPrécédent",
    "next": "→\nSuivant",
    "next-attention": "⚠\nAlerte",
}


def format_character_key(
    position: int | None,
    pseudo: str,
    character_class: str,
    alias: str,
) -> str:
    """Render the four default Stream Deck text lines for one character."""
    values = (
        "—" if position is None else str(position),
        pseudo.strip() or "—",
        character_class.strip() or "—",
        alias.strip() or "—",
    )
    return "\n".join(values)
