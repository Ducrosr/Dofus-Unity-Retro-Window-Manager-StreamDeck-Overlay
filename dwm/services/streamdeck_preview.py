from __future__ import annotations


STREAMDECK_PROFILE_LAYOUT: tuple[tuple[str | int, ...], ...] = (
    ("move-up", 1, 2, 3, 4),
    ("move-down", 5, 6, 7, 8),
    ("show", "toggle-ignore", "refresh", "previous", "next"),
)

STREAMDECK_ACTION_LABELS = {
    "move-up": "☰  ↑\nMonter",
    "move-down": "☰  ↓\nDescendre",
    "show": "DWM\nAfficher",
    "toggle-ignore": "⊘\nIgnorer",
    "refresh": "↻\nActualiser",
    "previous": "←\nPrécédent",
    "next": "→\nSuivant",
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
