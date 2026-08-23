from __future__ import annotations

from collections import OrderedDict
from collections.abc import Mapping


UNITY_STANDARD_THEME = "unity-standard"
RETRO_THEME = "dwm-retro"
LEGACY_THEME_ALIASES = {
    "dwm-dark": UNITY_STANDARD_THEME,
    "equilux": UNITY_STANDARD_THEME,
    "black": UNITY_STANDARD_THEME,
}

THEME_LABELS: "OrderedDict[str, str]" = OrderedDict(
    (
        (UNITY_STANDARD_THEME, "Standard"),
        ("unity-bonta", "Bonta"),
        ("unity-brakmar", "Brakmar"),
        ("unity-tribute", "Tribute"),
        ("unity-gold-steel", "Gold and Steel"),
        ("unity-belladone", "Belladone"),
        ("unity-unicorn", "Unicorn"),
        ("unity-emerald-mine", "Emerald Mine"),
        ("unity-sufokia", "Sufokia"),
        ("unity-pandala", "Pandala"),
        ("unity-wabbit", "Wabbit"),
        (RETRO_THEME, "Retro"),
    )
)

UNITY_THEME_IDS = tuple(theme for theme in THEME_LABELS if theme != RETRO_THEME)


def theme_ids_for_mode(game_mode: str) -> tuple[str, ...]:
    """Expose every built-in theme in both Unity and Retro modes."""
    return tuple(THEME_LABELS)


def _palette(
    *,
    bg: str,
    bg2: str,
    bg3: str,
    line: str,
    accent: str,
    header: str,
    fg: str = "#f4f4f2",
    muted: str = "#b9bec8",
) -> dict[str, str]:
    return {
        "bg": bg,
        "bg2": bg2,
        "bg3": bg3,
        "fg": fg,
        "muted": muted,
        "line": line,
        "accent": accent,
        "accent_hover": header,
        "accent_pressed": accent,
        "button_hover": header,
        "header": header,
        "on_dark": "#ffffff",
        "on_accent": "#17191d",
        "attention": "#f0a13a",
        "on_attention": "#17191d",
    }


THEME_PALETTES: Mapping[str, dict[str, str]] = {
    UNITY_STANDARD_THEME: _palette(
        bg="#191a2d", bg2="#292c4c", bg3="#3a3d58", line="#78789f",
        accent="#cbd750", header="#737298", muted="#b9bad5",
    ),
    "unity-bonta": _palette(
        bg="#25272e", bg2="#343842", bg3="#434a57", line="#7e8895",
        accent="#d7b384", header="#5c7caf", muted="#b9c4d2",
    ),
    "unity-brakmar": _palette(
        bg="#1c1c1c", bg2="#282828", bg3="#373535", line="#6d696a",
        accent="#d4af7e", header="#993c4b", muted="#c2b9b9",
    ),
    "unity-tribute": _palette(
        bg="#1f211b", bg2="#292c25", bg3="#373a30", line="#797d71",
        accent="#acc962", header="#777775", muted="#b9beaf",
    ),
    "unity-gold-steel": _palette(
        bg="#1e1e1e", bg2="#2b2825", bg3="#3b3630", line="#988f86",
        accent="#d6b180", header="#9f734f", muted="#c8beb2",
    ),
    "unity-belladone": _palette(
        bg="#221c2a", bg2="#332c3c", bg3="#423d53", line="#857693",
        accent="#bcc764", header="#867696", muted="#c5b9cf",
    ),
    "unity-unicorn": _palette(
        bg="#231f1f", bg2="#342d34", bg3="#493f49", line="#857583",
        accent="#d795c8", header="#8f5b90", muted="#cdbdca",
    ),
    "unity-emerald-mine": _palette(
        bg="#1c2322", bg2="#25302e", bg3="#293331", line="#6e8289",
        accent="#80cfb6", header="#5b878b", muted="#b5cbc7",
    ),
    "unity-sufokia": _palette(
        bg="#25272e", bg2="#343842", bg3="#434a57", line="#7e8895",
        accent="#d7cd84", header="#477d7f", muted="#bbc9cc",
    ),
    "unity-pandala": _palette(
        bg="#1e1e1e", bg2="#2c2d27", bg3="#3b3630", line="#8f9279",
        accent="#d6cb80", header="#6f8d4a", muted="#c2c6b0",
    ),
    "unity-wabbit": _palette(
        bg="#211f1b", bg2="#2d2b25", bg3="#373a30", line="#7e786d",
        accent="#acc862", header="#c16344", muted="#c6bdaf",
    ),
    RETRO_THEME: {
        "bg": "#d5d1b3",
        "bg2": "#c5ba9d",
        "bg3": "#50493a",
        "fg": "#332e27",
        "muted": "#6e6757",
        "line": "#948a6f",
        "accent": "#f27922",
        "accent_hover": "#ff963e",
        "accent_pressed": "#c85b17",
        "button_hover": "#655f4c",
        "header": "#3a352b",
        "on_dark": "#fffdf0",
        "on_accent": "#ffffff",
        "attention": "#e69949",
        "on_attention": "#332e27",
    },
}


def default_theme_for_mode(game_mode: str) -> str:
    return RETRO_THEME if (game_mode or "").strip().lower() == "retro" else UNITY_STANDARD_THEME


def normalize_theme(theme_name: str | None, game_mode: str = "unity") -> str:
    requested = (theme_name or "").strip().lower()
    requested = LEGACY_THEME_ALIASES.get(requested, requested)
    if requested in THEME_PALETTES:
        return requested
    return default_theme_for_mode(game_mode)


def theme_palette(theme_name: str | None, game_mode: str = "unity") -> dict[str, str]:
    return dict(THEME_PALETTES[normalize_theme(theme_name, game_mode)])


def theme_label(theme_name: str | None, game_mode: str = "unity") -> str:
    return THEME_LABELS[normalize_theme(theme_name, game_mode)]
