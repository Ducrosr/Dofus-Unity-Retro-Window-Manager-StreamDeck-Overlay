from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from ..services.display_overlay import (
    DEFAULT_ROTATION_OVERLAY_LAYOUT,
    clamp_notification_duration,
    clamp_overlay_opacity,
    normalize_overlay_anchor,
    normalize_overlay_layout,
)
from ..services.character_visuals import sanitize_character_visuals
from ..services.themes import (
    UNITY_STANDARD_THEME,
    default_theme_for_mode,
    normalize_theme,
)


SETTINGS_SCHEMA_VERSION = 16
MODERN_DARK_THEME = UNITY_STANDARD_THEME  # Backward-compatible public name.
DEFAULT_WINDOW_COLUMN_ORDER = ("class", "name", "alias", "hwnd")


@dataclass
class Settings:
    # UI
    theme: str = ""
    theme_by_game_mode: dict[str, str] | None = None
    language: str = "fr"
    window_column_order: list[str] | None = None
    minimize_to_tray: bool = True
    start_with_windows: bool = False
    check_updates_automatically: bool = True
    include_prereleases: bool = True
    last_update_check_at: str = ""
    compact_window_geometry: str = ""
    swap_notification_enabled: bool = True
    swap_notification_anchor: str = "top_center"
    swap_notification_duration_ms: int = 1400
    swap_notification_opacity: int = 96
    swap_notification_layout: dict[str, str] | None = None
    rotation_overlay_enabled: bool = False
    rotation_overlay_x: int = 24
    rotation_overlay_y: int = 160
    rotation_overlay_opacity: int = 88
    rotation_overlay_locked: bool = False
    rotation_overlay_layout: dict[str, str] | None = None
    rotation_overlay_width: int = 300
    rotation_overlay_auto_width: bool = True
    rotation_overlay_height: int = 0
    attention_blink_enabled: bool = True
    show_popup_portraits: bool = True
    show_popup_badges: bool = True
    show_overlay_portraits: bool = True
    show_overlay_badges: bool = True
    show_character_portraits: bool = True
    show_character_badges: bool = True
    character_visuals: dict[str, dict[str, str]] | None = None

    # Refresh
    auto_refresh: bool = True
    refresh_seconds: int = 10

    # Keep the window list in sync via WinEventHook (no polling required).
    # (no polling scans required)
    event_hook_enabled: bool = True

    # Retro popup watcher (Groupe/Echange modal dialogs)
    popup_watch_enabled: bool = False

    # Hotkeys
    hotkeys: Dict[str, str] | None = None

    # Profiles
    last_profile: str = ""

    # Game selection
    game_mode: str = "unity"  # "unity" | "retro"

    # Retro detection heuristics (Chrome_WidgetWin_1 is shared by many apps)
    # By default we enforce the known Retro marker in the window title to avoid
    # false positives from other Chromium/Electron apps using Chrome_WidgetWin_1.
    retro_title_keyword: str = "dofus retro v"
    retro_process_keyword: str = ""

    def reset_display_preferences(self, game_mode: str | None = None) -> None:
        """Restore UI/overlay defaults without deleting profiles or character visuals."""
        mode = (game_mode or self.game_mode or "unity").strip().lower()
        if mode not in {"unity", "retro"}:
            mode = "unity"
        self.game_mode = mode
        self.theme_by_game_mode = {
            "unity": default_theme_for_mode("unity"),
            "retro": default_theme_for_mode("retro"),
        }
        self.theme = self.theme_by_game_mode[mode]
        self.window_column_order = list(DEFAULT_WINDOW_COLUMN_ORDER)
        self.compact_window_geometry = ""
        self.swap_notification_enabled = True
        self.swap_notification_anchor = "top_center"
        self.swap_notification_duration_ms = 1400
        self.swap_notification_opacity = 96
        self.swap_notification_layout = dict(DEFAULT_ROTATION_OVERLAY_LAYOUT)
        self.rotation_overlay_enabled = False
        self.rotation_overlay_x = 24
        self.rotation_overlay_y = 160
        self.rotation_overlay_opacity = 88
        self.rotation_overlay_locked = False
        self.rotation_overlay_layout = dict(DEFAULT_ROTATION_OVERLAY_LAYOUT)
        self.rotation_overlay_width = 300
        self.rotation_overlay_auto_width = True
        self.rotation_overlay_height = 0
        self.attention_blink_enabled = True
        self.show_popup_portraits = True
        self.show_popup_badges = True
        self.show_overlay_portraits = True
        self.show_overlay_badges = True
        self.show_character_portraits = True
        self.show_character_badges = True

    def __post_init__(self):
        requested_columns = self.window_column_order or []
        normalized_columns: list[str] = []
        for column in (*requested_columns, *DEFAULT_WINDOW_COLUMN_ORDER):
            if column in DEFAULT_WINDOW_COLUMN_ORDER and column not in normalized_columns:
                normalized_columns.append(column)
        self.window_column_order = normalized_columns

        if self.hotkeys is None:
            self.hotkeys = {}
        # Ensure required hotkeys exist (backward compatible)
        defaults = {
            "forward": "F5",
            "backward": "F6",
            "ignore": "F7",
            "next_attention": "F8",
            "refresh": "Ctrl+Alt+R",
        }
        for k, v in defaults.items():
            if not (self.hotkeys or {}).get(k):
                self.hotkeys[k] = v

        gm = (self.game_mode or "unity").strip().lower()
        if gm not in ("unity", "retro"):
            gm = "unity"
        self.game_mode = gm

        language = (self.language or "fr").strip().lower()
        self.language = language if language in {"fr", "en", "es"} else "fr"

        remembered_themes = dict(self.theme_by_game_mode or {})
        legacy_theme = normalize_theme(self.theme, gm)
        remembered_themes[gm] = normalize_theme(remembered_themes.get(gm, legacy_theme), gm)
        for mode in ("unity", "retro"):
            remembered_themes[mode] = normalize_theme(
                remembered_themes.get(mode, default_theme_for_mode(mode)),
                mode,
            )
        self.theme_by_game_mode = remembered_themes
        self.theme = remembered_themes[gm]

        # Normalize keywords
        self.retro_title_keyword = (self.retro_title_keyword or "dofus retro v").strip().lower()
        # Allow empty process keyword (we prefer strict title matching).
        self.retro_process_keyword = (self.retro_process_keyword or "").strip().lower()

        self.compact_window_geometry = (self.compact_window_geometry or "").strip()
        self.swap_notification_anchor = normalize_overlay_anchor(self.swap_notification_anchor)
        self.swap_notification_duration_ms = clamp_notification_duration(self.swap_notification_duration_ms)
        self.swap_notification_opacity = clamp_overlay_opacity(self.swap_notification_opacity)
        self.swap_notification_layout = normalize_overlay_layout(self.swap_notification_layout)
        self.rotation_overlay_opacity = clamp_overlay_opacity(self.rotation_overlay_opacity)
        self.rotation_overlay_layout = normalize_overlay_layout(self.rotation_overlay_layout)
        try:
            self.rotation_overlay_width = max(80, min(900, int(self.rotation_overlay_width)))
            requested_height = int(self.rotation_overlay_height)
            self.rotation_overlay_height = 0 if requested_height <= 0 else max(80, min(1600, requested_height))
        except (TypeError, ValueError):
            self.rotation_overlay_width = 300
            self.rotation_overlay_height = 0
        self.character_visuals = sanitize_character_visuals(self.character_visuals)
        try:
            self.rotation_overlay_x = int(self.rotation_overlay_x)
            self.rotation_overlay_y = int(self.rotation_overlay_y)
        except (TypeError, ValueError):
            self.rotation_overlay_x = 24
            self.rotation_overlay_y = 160

    def to_dict(self) -> dict:
        return {
            "schema_version": SETTINGS_SCHEMA_VERSION,
            "theme": self.theme,
            "theme_by_game_mode": dict(self.theme_by_game_mode or {}),
            "language": self.language,
            "window_column_order": list(self.window_column_order or DEFAULT_WINDOW_COLUMN_ORDER),
            "minimize_to_tray": bool(self.minimize_to_tray),
            "start_with_windows": bool(self.start_with_windows),
            "check_updates_automatically": bool(self.check_updates_automatically),
            "include_prereleases": bool(self.include_prereleases),
            "last_update_check_at": self.last_update_check_at,
            "compact_window_geometry": self.compact_window_geometry,
            "swap_notification_enabled": bool(self.swap_notification_enabled),
            "swap_notification_anchor": self.swap_notification_anchor,
            "swap_notification_duration_ms": int(self.swap_notification_duration_ms),
            "swap_notification_opacity": int(self.swap_notification_opacity),
            "swap_notification_layout": dict(
                self.swap_notification_layout or DEFAULT_ROTATION_OVERLAY_LAYOUT
            ),
            "rotation_overlay_enabled": bool(self.rotation_overlay_enabled),
            "rotation_overlay_x": int(self.rotation_overlay_x),
            "rotation_overlay_y": int(self.rotation_overlay_y),
            "rotation_overlay_opacity": int(self.rotation_overlay_opacity),
            "rotation_overlay_locked": bool(self.rotation_overlay_locked),
            "rotation_overlay_layout": dict(
                self.rotation_overlay_layout or DEFAULT_ROTATION_OVERLAY_LAYOUT
            ),
            "rotation_overlay_width": int(self.rotation_overlay_width),
            "rotation_overlay_auto_width": bool(self.rotation_overlay_auto_width),
            "rotation_overlay_height": int(self.rotation_overlay_height),
            "attention_blink_enabled": bool(self.attention_blink_enabled),
            "show_popup_portraits": bool(self.show_popup_portraits),
            "show_popup_badges": bool(self.show_popup_badges),
            "show_overlay_portraits": bool(self.show_overlay_portraits),
            "show_overlay_badges": bool(self.show_overlay_badges),
            "show_character_portraits": bool(self.show_character_portraits),
            "show_character_badges": bool(self.show_character_badges),
            "character_visuals": sanitize_character_visuals(self.character_visuals),
            "auto_refresh": self.auto_refresh,
            "refresh_seconds": int(self.refresh_seconds),
            "event_hook_enabled": bool(self.event_hook_enabled),
            "popup_watch_enabled": bool(getattr(self, "popup_watch_enabled", False)),
            "hotkeys": dict(self.hotkeys or {}),
            "last_profile": self.last_profile,
            "game_mode": self.game_mode,
            "retro_title_keyword": self.retro_title_keyword,
            "retro_process_keyword": self.retro_process_keyword,
        }

    @staticmethod
    def from_dict(d: dict) -> "Settings":
        # Backward compatible: schema v1 had no game info.
        schema = int(d.get("schema_version", 1) or 1)

        # Migration: old defaults were too broad ("dofus"), leading to false positives.
        retro_title = (d.get("retro_title_keyword") or "").strip().lower()
        retro_proc = (d.get("retro_process_keyword") or "").strip().lower()

        if schema < 3 and (not retro_title or retro_title == "dofus"):
            retro_title = "dofus retro v"
        # Keep empty process keyword by default in v3.
        if schema < 3 and retro_proc == "dofus":
            retro_proc = ""

        # Equilux was the historical default. Existing installations using that
        # default move to DWM's modern dark theme, while explicit alternatives
        # remain untouched.
        stored_game_mode = str(d.get("game_mode") or "unity")
        theme = (d.get("theme") or default_theme_for_mode(stored_game_mode)).strip()
        if schema < 8 and theme == "equilux":
            theme = UNITY_STANDARD_THEME

        legacy_portraits = bool(d.get("show_character_portraits", True))
        legacy_badges = bool(d.get("show_character_badges", True))
        legacy_overlay_width = int(d.get("rotation_overlay_width", 300))
        auto_width_default = not (schema < 16 and legacy_overlay_width != 300)

        return Settings(
            theme=theme,
            theme_by_game_mode=d.get("theme_by_game_mode") or None,
            language=str(d.get("language") or "fr"),
            window_column_order=d.get("window_column_order") or None,
            minimize_to_tray=bool(d.get("minimize_to_tray", True)),
            start_with_windows=bool(d.get("start_with_windows", False)),
            check_updates_automatically=bool(d.get("check_updates_automatically", True)),
            include_prereleases=bool(d.get("include_prereleases", True)),
            last_update_check_at=str(d.get("last_update_check_at") or ""),
            compact_window_geometry=str(d.get("compact_window_geometry") or ""),
            swap_notification_enabled=bool(d.get("swap_notification_enabled", True)),
            swap_notification_anchor=str(d.get("swap_notification_anchor") or "top_center"),
            swap_notification_duration_ms=int(d.get("swap_notification_duration_ms", 1400)),
            swap_notification_opacity=int(d.get("swap_notification_opacity", 96)),
            swap_notification_layout=d.get("swap_notification_layout") or None,
            rotation_overlay_enabled=bool(d.get("rotation_overlay_enabled", False)),
            rotation_overlay_x=int(d.get("rotation_overlay_x", 24)),
            rotation_overlay_y=int(d.get("rotation_overlay_y", 160)),
            rotation_overlay_opacity=int(d.get("rotation_overlay_opacity", 88)),
            rotation_overlay_locked=bool(d.get("rotation_overlay_locked", False)),
            rotation_overlay_layout=d.get("rotation_overlay_layout") or None,
            rotation_overlay_width=legacy_overlay_width,
            rotation_overlay_auto_width=bool(
                d.get("rotation_overlay_auto_width", auto_width_default)
            ),
            rotation_overlay_height=int(d.get("rotation_overlay_height", 0)),
            attention_blink_enabled=bool(d.get("attention_blink_enabled", True)),
            show_popup_portraits=bool(d.get("show_popup_portraits", legacy_portraits)),
            show_popup_badges=bool(d.get("show_popup_badges", legacy_badges)),
            show_overlay_portraits=bool(d.get("show_overlay_portraits", legacy_portraits)),
            show_overlay_badges=bool(d.get("show_overlay_badges", legacy_badges)),
            show_character_portraits=legacy_portraits,
            show_character_badges=legacy_badges,
            character_visuals=d.get("character_visuals") or None,
            auto_refresh=bool(d.get("auto_refresh", True)),
            refresh_seconds=int(d.get("refresh_seconds", 10)),
            event_hook_enabled=bool(d.get("event_hook_enabled", True)),
            popup_watch_enabled=bool(d.get("popup_watch_enabled", False)),
            hotkeys=d.get("hotkeys") or None,
            last_profile=d.get("last_profile", ""),
            game_mode=stored_game_mode,
            retro_title_keyword=retro_title or "dofus retro v",
            retro_process_keyword=retro_proc,
        )


def load_settings(path: Path) -> Settings:
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return Settings.from_dict(data)
    except Exception:
        pass
    return Settings()


def save_settings(path: Path, settings: Settings) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(settings.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
