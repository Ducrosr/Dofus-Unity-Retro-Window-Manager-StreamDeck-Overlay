from __future__ import annotations

import unittest

from dwm.services.themes import (
    RETRO_THEME,
    THEME_LABELS,
    THEME_PALETTES,
    UNITY_STANDARD_THEME,
    default_theme_for_mode,
    normalize_theme,
    theme_ids_for_mode,
)


class ThemeTests(unittest.TestCase):
    def test_eleven_unity_themes_and_retro_are_available(self) -> None:
        self.assertEqual(len(THEME_LABELS), 12)
        self.assertEqual(set(THEME_LABELS), set(THEME_PALETTES))

    def test_defaults_follow_game_mode(self) -> None:
        self.assertEqual(default_theme_for_mode("unity"), UNITY_STANDARD_THEME)
        self.assertEqual(default_theme_for_mode("retro"), RETRO_THEME)

    def test_settings_offer_every_theme_in_both_game_modes(self) -> None:
        expected = tuple(THEME_LABELS)
        self.assertEqual(theme_ids_for_mode("unity"), expected)
        self.assertEqual(theme_ids_for_mode("retro"), expected)
        self.assertIn(RETRO_THEME, theme_ids_for_mode("unity"))
        self.assertIn(UNITY_STANDARD_THEME, theme_ids_for_mode("retro"))

    def test_legacy_and_removed_themes_are_migrated(self) -> None:
        self.assertEqual(normalize_theme("dwm-dark", "unity"), UNITY_STANDARD_THEME)
        self.assertEqual(normalize_theme("arc", "retro"), RETRO_THEME)
