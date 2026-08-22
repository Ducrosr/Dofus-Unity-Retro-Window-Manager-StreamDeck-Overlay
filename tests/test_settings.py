from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dwm.storage.settings import (
    DEFAULT_WINDOW_COLUMN_ORDER,
    MODERN_DARK_THEME,
    Settings,
    load_settings,
    save_settings,
)


class SettingsTests(unittest.TestCase):
    def test_defaults_are_complete(self) -> None:
        settings = Settings()
        self.assertEqual(settings.game_mode, "unity")
        self.assertEqual(settings.hotkeys["forward"], "F5")
        self.assertEqual(settings.hotkeys["refresh"], "Ctrl+Alt+R")
        self.assertEqual(settings.window_column_order, list(DEFAULT_WINDOW_COLUMN_ORDER))
        self.assertEqual(settings.theme, MODERN_DARK_THEME)
        self.assertTrue(settings.minimize_to_tray)
        self.assertFalse(settings.start_with_windows)

    def test_column_order_is_sanitized_and_completed(self) -> None:
        settings = Settings(window_column_order=["alias", "invalid", "class", "alias"])

        self.assertEqual(settings.window_column_order, ["alias", "class", "name", "hwnd"])

    def test_old_retro_filter_is_migrated(self) -> None:
        settings = Settings.from_dict(
            {
                "schema_version": 2,
                "retro_title_keyword": "dofus",
                "retro_process_keyword": "dofus",
            }
        )
        self.assertEqual(settings.retro_title_keyword, "dofus retro v")
        self.assertEqual(settings.retro_process_keyword, "")

    def test_historical_default_theme_is_migrated(self) -> None:
        settings = Settings.from_dict({"schema_version": 7, "theme": "equilux"})

        self.assertEqual(settings.theme, MODERN_DARK_THEME)

    def test_explicit_alternative_theme_is_preserved(self) -> None:
        settings = Settings.from_dict({"schema_version": 7, "theme": "arc"})

        self.assertEqual(settings.theme, "arc")

    def test_save_then_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            expected = Settings(
                game_mode="retro",
                refresh_seconds=7,
                last_profile="Équipe",
                window_column_order=["name", "alias", "class", "hwnd"],
            )
            save_settings(path, expected)
            actual = load_settings(path)

        self.assertEqual(actual.game_mode, "retro")
        self.assertEqual(actual.refresh_seconds, 7)
        self.assertEqual(actual.last_profile, "Équipe")
        self.assertEqual(actual.window_column_order, ["name", "alias", "class", "hwnd"])


if __name__ == "__main__":
    unittest.main()
