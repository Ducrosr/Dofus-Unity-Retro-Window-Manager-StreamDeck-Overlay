from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


SETTINGS_SCHEMA_VERSION = 9
MODERN_DARK_THEME = "dwm-dark"
DEFAULT_WINDOW_COLUMN_ORDER = ("class", "name", "alias", "hwnd")


@dataclass
class Settings:
    # UI
    theme: str = MODERN_DARK_THEME
    window_column_order: list[str] | None = None
    minimize_to_tray: bool = True
    start_with_windows: bool = False

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
            "refresh": "Ctrl+Alt+R",
        }
        for k, v in defaults.items():
            if not (self.hotkeys or {}).get(k):
                self.hotkeys[k] = v

        gm = (self.game_mode or "unity").strip().lower()
        if gm not in ("unity", "retro"):
            gm = "unity"
        self.game_mode = gm

        # Normalize keywords
        self.retro_title_keyword = (self.retro_title_keyword or "dofus retro v").strip().lower()
        # Allow empty process keyword (we prefer strict title matching).
        self.retro_process_keyword = (self.retro_process_keyword or "").strip().lower()

    def to_dict(self) -> dict:
        return {
            "schema_version": SETTINGS_SCHEMA_VERSION,
            "theme": self.theme,
            "window_column_order": list(self.window_column_order or DEFAULT_WINDOW_COLUMN_ORDER),
            "minimize_to_tray": bool(self.minimize_to_tray),
            "start_with_windows": bool(self.start_with_windows),
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
        theme = (d.get("theme") or MODERN_DARK_THEME).strip()
        if schema < 8 and theme == "equilux":
            theme = MODERN_DARK_THEME

        return Settings(
            theme=theme,
            window_column_order=d.get("window_column_order") or None,
            minimize_to_tray=bool(d.get("minimize_to_tray", True)),
            start_with_windows=bool(d.get("start_with_windows", False)),
            auto_refresh=bool(d.get("auto_refresh", True)),
            refresh_seconds=int(d.get("refresh_seconds", 10)),
            event_hook_enabled=bool(d.get("event_hook_enabled", True)),
            popup_watch_enabled=bool(d.get("popup_watch_enabled", False)),
            hotkeys=d.get("hotkeys") or None,
            last_profile=d.get("last_profile", ""),
            game_mode=(d.get("game_mode") or "unity"),
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
