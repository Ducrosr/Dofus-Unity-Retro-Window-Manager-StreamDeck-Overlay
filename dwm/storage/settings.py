from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from ..services.display_overlay import (
    DEFAULT_ROTATION_OVERLAY_LAYOUT,
    clamp_notification_duration,
    clamp_overlay_opacity,
    normalize_overlay_anchor,
    normalize_overlay_orientation,
    normalize_overlay_layout,
)
from ..services.character_visuals import sanitize_character_visuals
from ..services.accessibility import clamp_ui_scale_percent
from ..services.themes import (
    UNITY_STANDARD_THEME,
    default_theme_for_mode,
    normalize_theme,
)
from .atomic import atomic_write_text


SETTINGS_SCHEMA_VERSION = 23
MODERN_DARK_THEME = UNITY_STANDARD_THEME  # Backward-compatible public name.
DEFAULT_WINDOW_COLUMN_ORDER = ("class", "name", "alias", "hwnd")


def _default_display_preferences() -> dict[str, object]:
    return {
        "compact_window_geometry": "",
        "swap_notification_enabled": True,
        "swap_notification_anchor": "top_center",
        "swap_notification_duration_ms": 1400,
        "swap_notification_opacity": 88,
        "swap_notification_layout": dict(DEFAULT_ROTATION_OVERLAY_LAYOUT),
        "rotation_overlay_enabled": True,
        "rotation_overlay_x": 24,
        "rotation_overlay_y": 160,
        "rotation_overlay_opacity": 88,
        "rotation_overlay_locked": False,
        "rotation_overlay_layout": dict(DEFAULT_ROTATION_OVERLAY_LAYOUT),
        "rotation_overlay_width": 300,
        "rotation_overlay_auto_width": True,
        "rotation_overlay_height": 0,
        "rotation_overlay_orientation": "vertical",
        "rotation_overlay_show_title": True,
        "rotation_overlay_show_reorder_buttons": True,
        "attention_blink_enabled": True,
        "show_popup_portraits": True,
        "show_popup_badges": True,
        "show_overlay_portraits": True,
        "show_overlay_badges": True,
        "show_character_portraits": True,
        "show_character_badges": True,
    }


def _normalized_display_preferences(
    value: object,
    *,
    fallback: Mapping[str, object] | None = None,
) -> dict[str, object]:
    raw = value if isinstance(value, Mapping) else {}
    base = dict(_default_display_preferences())
    if fallback:
        base.update(fallback)
    base.update(raw)

    def safe_int(key: str, default: int) -> int:
        try:
            return int(base.get(key, default))
        except (TypeError, ValueError):
            return default

    requested_height = safe_int("rotation_overlay_height", 0)
    return {
        "compact_window_geometry": str(base.get("compact_window_geometry") or "").strip(),
        "swap_notification_enabled": bool(base.get("swap_notification_enabled", True)),
        "swap_notification_anchor": normalize_overlay_anchor(
            str(base.get("swap_notification_anchor") or "top_center")
        ),
        "swap_notification_duration_ms": clamp_notification_duration(
            base.get("swap_notification_duration_ms", 1400)
        ),
        "swap_notification_opacity": clamp_overlay_opacity(
            base.get("swap_notification_opacity", 88)
        ),
        "swap_notification_layout": normalize_overlay_layout(
            base.get("swap_notification_layout")
        ),
        "rotation_overlay_enabled": bool(base.get("rotation_overlay_enabled", True)),
        "rotation_overlay_x": safe_int("rotation_overlay_x", 24),
        "rotation_overlay_y": safe_int("rotation_overlay_y", 160),
        "rotation_overlay_opacity": clamp_overlay_opacity(
            base.get("rotation_overlay_opacity", 88)
        ),
        "rotation_overlay_locked": bool(base.get("rotation_overlay_locked", False)),
        "rotation_overlay_layout": normalize_overlay_layout(
            base.get("rotation_overlay_layout")
        ),
        "rotation_overlay_width": max(
            80,
            min(1800, safe_int("rotation_overlay_width", 300)),
        ),
        "rotation_overlay_auto_width": bool(
            base.get("rotation_overlay_auto_width", True)
        ),
        "rotation_overlay_height": (
            0 if requested_height <= 0 else max(80, min(1600, requested_height))
        ),
        "rotation_overlay_orientation": normalize_overlay_orientation(
            base.get("rotation_overlay_orientation")
        ),
        "rotation_overlay_show_title": bool(
            base.get("rotation_overlay_show_title", True)
        ),
        "rotation_overlay_show_reorder_buttons": bool(
            base.get("rotation_overlay_show_reorder_buttons", True)
        ),
        "attention_blink_enabled": bool(base.get("attention_blink_enabled", True)),
        "show_popup_portraits": bool(base.get("show_popup_portraits", True)),
        "show_popup_badges": bool(base.get("show_popup_badges", True)),
        "show_overlay_portraits": bool(base.get("show_overlay_portraits", True)),
        "show_overlay_badges": bool(base.get("show_overlay_badges", True)),
        "show_character_portraits": bool(base.get("show_character_portraits", True)),
        "show_character_badges": bool(base.get("show_character_badges", True)),
    }


@dataclass
class Settings:
    # UI
    theme: str = ""
    theme_by_game_mode: dict[str, str] | None = None
    display_by_game_mode: dict[str, dict[str, object]] | None = None
    language: str = "fr"
    security_notice_accepted: bool = False
    onboarding_completed: bool = False
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
    swap_notification_opacity: int = 88
    swap_notification_layout: dict[str, str] | None = None
    rotation_overlay_enabled: bool = True
    rotation_overlay_x: int = 24
    rotation_overlay_y: int = 160
    rotation_overlay_opacity: int = 88
    rotation_overlay_locked: bool = False
    rotation_overlay_layout: dict[str, str] | None = None
    rotation_overlay_width: int = 300
    rotation_overlay_auto_width: bool = True
    rotation_overlay_height: int = 0
    rotation_overlay_orientation: str = "vertical"
    rotation_overlay_show_title: bool = True
    rotation_overlay_show_reorder_buttons: bool = True
    attention_blink_enabled: bool = True
    show_popup_portraits: bool = True
    show_popup_badges: bool = True
    show_overlay_portraits: bool = True
    show_overlay_badges: bool = True
    show_character_portraits: bool = True
    show_character_badges: bool = True
    character_visuals: dict[str, dict[str, str]] | None = None
    accessibility_high_contrast: bool = False
    accessibility_reduce_motion: bool = False
    accessibility_ui_scale_percent: int = 100

    # Refresh
    auto_refresh: bool = True
    refresh_seconds: int = 10
    adaptive_performance_enabled: bool = True

    # Keep the window list in sync via WinEventHook (no polling required).
    # (no polling scans required)
    event_hook_enabled: bool = True

    # Retro popup watcher (Groupe/Echange modal dialogs)
    popup_watch_enabled: bool = False

    # Hotkeys
    hotkeys: Dict[str, str] | None = None

    # Profiles
    last_profile: str = ""
    smart_profile_loading_enabled: bool = True

    # Game selection
    game_mode: str = "unity"  # "unity" | "retro"

    # Retro detection heuristics (Chrome_WidgetWin_1 is shared by many apps)
    # By default we enforce the known Retro marker in the window title to avoid
    # false positives from other Chromium/Electron apps using Chrome_WidgetWin_1.
    retro_title_keyword: str = "dofus retro v"
    retro_process_keyword: str = ""

    def reset_display_preferences(self, game_mode: str | None = None) -> None:
        """Restore display defaults for one game mode without touching user profiles."""
        mode = (game_mode or self.game_mode or "unity").strip().lower()
        if mode not in {"unity", "retro"}:
            mode = "unity"
        self.game_mode = mode
        self.theme_by_game_mode = dict(self.theme_by_game_mode or {})
        self.theme_by_game_mode[mode] = default_theme_for_mode(mode)
        self.theme = self.theme_by_game_mode[mode]
        self.window_column_order = list(DEFAULT_WINDOW_COLUMN_ORDER)
        display_modes = dict(self.display_by_game_mode or {})
        display_modes[mode] = _default_display_preferences()
        self.display_by_game_mode = display_modes
        self.activate_display_preferences(mode)

    def _display_preferences_snapshot(self) -> dict[str, object]:
        return _normalized_display_preferences(
            {
                "compact_window_geometry": self.compact_window_geometry,
                "swap_notification_enabled": self.swap_notification_enabled,
                "swap_notification_anchor": self.swap_notification_anchor,
                "swap_notification_duration_ms": self.swap_notification_duration_ms,
                "swap_notification_opacity": self.swap_notification_opacity,
                "swap_notification_layout": self.swap_notification_layout,
                "rotation_overlay_enabled": self.rotation_overlay_enabled,
                "rotation_overlay_x": self.rotation_overlay_x,
                "rotation_overlay_y": self.rotation_overlay_y,
                "rotation_overlay_opacity": self.rotation_overlay_opacity,
                "rotation_overlay_locked": self.rotation_overlay_locked,
                "rotation_overlay_layout": self.rotation_overlay_layout,
                "rotation_overlay_width": self.rotation_overlay_width,
                "rotation_overlay_auto_width": self.rotation_overlay_auto_width,
                "rotation_overlay_height": self.rotation_overlay_height,
                "rotation_overlay_orientation": self.rotation_overlay_orientation,
                "rotation_overlay_show_title": self.rotation_overlay_show_title,
                "rotation_overlay_show_reorder_buttons": self.rotation_overlay_show_reorder_buttons,
                "attention_blink_enabled": self.attention_blink_enabled,
                "show_popup_portraits": self.show_popup_portraits,
                "show_popup_badges": self.show_popup_badges,
                "show_overlay_portraits": self.show_overlay_portraits,
                "show_overlay_badges": self.show_overlay_badges,
                "show_character_portraits": self.show_character_portraits,
                "show_character_badges": self.show_character_badges,
            }
        )

    def remember_display_preferences(self, game_mode: str | None = None) -> None:
        mode = (game_mode or self.game_mode or "unity").strip().lower()
        if mode not in {"unity", "retro"}:
            mode = "unity"
        remembered = dict(self.display_by_game_mode or {})
        remembered[mode] = self._display_preferences_snapshot()
        self.display_by_game_mode = remembered

    def activate_display_preferences(self, game_mode: str | None = None) -> None:
        mode = (game_mode or self.game_mode or "unity").strip().lower()
        if mode not in {"unity", "retro"}:
            mode = "unity"
        preferences = _normalized_display_preferences(
            (self.display_by_game_mode or {}).get(mode)
        )
        for key, value in preferences.items():
            setattr(self, key, value)
        remembered = dict(self.display_by_game_mode or {})
        remembered[mode] = preferences
        self.display_by_game_mode = remembered

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
        for position in range(1, 9):
            self.hotkeys.setdefault(f"window_{position}", "")

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
        self.rotation_overlay_orientation = normalize_overlay_orientation(
            self.rotation_overlay_orientation
        )
        try:
            self.rotation_overlay_width = max(80, min(1800, int(self.rotation_overlay_width)))
            requested_height = int(self.rotation_overlay_height)
            self.rotation_overlay_height = 0 if requested_height <= 0 else max(80, min(1600, requested_height))
        except (TypeError, ValueError):
            self.rotation_overlay_width = 300
            self.rotation_overlay_height = 0
        self.character_visuals = sanitize_character_visuals(self.character_visuals)
        self.accessibility_ui_scale_percent = clamp_ui_scale_percent(
            self.accessibility_ui_scale_percent
        )
        try:
            self.rotation_overlay_x = int(self.rotation_overlay_x)
            self.rotation_overlay_y = int(self.rotation_overlay_y)
        except (TypeError, ValueError):
            self.rotation_overlay_x = 24
            self.rotation_overlay_y = 160

        legacy_display = self._display_preferences_snapshot()
        raw_display_modes = (
            self.display_by_game_mode
            if isinstance(self.display_by_game_mode, Mapping)
            else {}
        )
        self.display_by_game_mode = {
            mode: _normalized_display_preferences(
                raw_display_modes.get(mode),
                fallback=(legacy_display if mode == gm else None),
            )
            for mode in ("unity", "retro")
        }
        self.activate_display_preferences(gm)

    def to_dict(self) -> dict:
        display_modes = {
            mode: _normalized_display_preferences(
                (self.display_by_game_mode or {}).get(mode)
            )
            for mode in ("unity", "retro")
        }
        display_modes[self.game_mode] = self._display_preferences_snapshot()
        return {
            "schema_version": SETTINGS_SCHEMA_VERSION,
            "theme": self.theme,
            "theme_by_game_mode": dict(self.theme_by_game_mode or {}),
            "display_by_game_mode": display_modes,
            "language": self.language,
            "security_notice_accepted": bool(self.security_notice_accepted),
            "onboarding_completed": bool(self.onboarding_completed),
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
            "rotation_overlay_orientation": self.rotation_overlay_orientation,
            "rotation_overlay_show_title": bool(self.rotation_overlay_show_title),
            "rotation_overlay_show_reorder_buttons": bool(
                self.rotation_overlay_show_reorder_buttons
            ),
            "attention_blink_enabled": bool(self.attention_blink_enabled),
            "show_popup_portraits": bool(self.show_popup_portraits),
            "show_popup_badges": bool(self.show_popup_badges),
            "show_overlay_portraits": bool(self.show_overlay_portraits),
            "show_overlay_badges": bool(self.show_overlay_badges),
            "show_character_portraits": bool(self.show_character_portraits),
            "show_character_badges": bool(self.show_character_badges),
            "character_visuals": sanitize_character_visuals(self.character_visuals),
            "accessibility_high_contrast": bool(self.accessibility_high_contrast),
            "accessibility_reduce_motion": bool(self.accessibility_reduce_motion),
            "accessibility_ui_scale_percent": int(self.accessibility_ui_scale_percent),
            "auto_refresh": self.auto_refresh,
            "refresh_seconds": int(self.refresh_seconds),
            "adaptive_performance_enabled": bool(self.adaptive_performance_enabled),
            "event_hook_enabled": bool(self.event_hook_enabled),
            "popup_watch_enabled": bool(getattr(self, "popup_watch_enabled", False)),
            "hotkeys": dict(self.hotkeys or {}),
            "last_profile": self.last_profile,
            "smart_profile_loading_enabled": bool(self.smart_profile_loading_enabled),
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
            display_by_game_mode=d.get("display_by_game_mode") or None,
            language=str(d.get("language") or "fr"),
            security_notice_accepted=bool(d.get("security_notice_accepted", False)),
            onboarding_completed=bool(
                d.get("onboarding_completed", schema < SETTINGS_SCHEMA_VERSION)
            ),
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
            swap_notification_opacity=int(
                d.get("swap_notification_opacity", 88 if schema >= 17 else 96)
            ),
            swap_notification_layout=d.get("swap_notification_layout") or None,
            rotation_overlay_enabled=bool(
                d.get("rotation_overlay_enabled", schema >= 17)
            ),
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
            rotation_overlay_orientation=str(
                d.get("rotation_overlay_orientation") or "vertical"
            ),
            rotation_overlay_show_title=bool(
                d.get("rotation_overlay_show_title", True)
            ),
            rotation_overlay_show_reorder_buttons=bool(
                d.get("rotation_overlay_show_reorder_buttons", True)
            ),
            attention_blink_enabled=bool(d.get("attention_blink_enabled", True)),
            show_popup_portraits=bool(d.get("show_popup_portraits", legacy_portraits)),
            show_popup_badges=bool(d.get("show_popup_badges", legacy_badges)),
            show_overlay_portraits=bool(d.get("show_overlay_portraits", legacy_portraits)),
            show_overlay_badges=bool(d.get("show_overlay_badges", legacy_badges)),
            show_character_portraits=legacy_portraits,
            show_character_badges=legacy_badges,
            character_visuals=d.get("character_visuals") or None,
            accessibility_high_contrast=bool(
                d.get("accessibility_high_contrast", False)
            ),
            accessibility_reduce_motion=bool(
                d.get("accessibility_reduce_motion", False)
            ),
            accessibility_ui_scale_percent=int(
                d.get("accessibility_ui_scale_percent", 100)
            ),
            auto_refresh=bool(d.get("auto_refresh", True)),
            refresh_seconds=int(d.get("refresh_seconds", 10)),
            adaptive_performance_enabled=bool(
                d.get("adaptive_performance_enabled", True)
            ),
            event_hook_enabled=bool(d.get("event_hook_enabled", True)),
            popup_watch_enabled=bool(d.get("popup_watch_enabled", False)),
            hotkeys=d.get("hotkeys") or None,
            last_profile=d.get("last_profile", ""),
            smart_profile_loading_enabled=bool(
                d.get("smart_profile_loading_enabled", True)
            ),
            game_mode=stored_game_mode,
            retro_title_keyword=retro_title or "dofus retro v",
            retro_process_keyword=retro_proc,
        )


def settings_backup_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.bak")


def _read_settings(path: Path) -> Settings:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("settings root must be a JSON object")
    return Settings.from_dict(data)


def load_settings(path: Path) -> Settings:
    for candidate in (path, settings_backup_path(path)):
        try:
            if candidate.exists():
                return _read_settings(candidate)
        except Exception:
            continue
    return Settings()


def save_settings(path: Path, settings: Settings) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(settings.to_dict(), indent=2, ensure_ascii=False)

    try:
        current = path.read_text(encoding="utf-8")
        if not isinstance(json.loads(current), dict):
            raise ValueError("settings root must be a JSON object")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        pass
    else:
        atomic_write_text(settings_backup_path(path), current)

    atomic_write_text(path, serialized)
