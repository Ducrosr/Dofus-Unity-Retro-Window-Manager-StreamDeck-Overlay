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
    @staticmethod
    def _contrast_ratio(foreground: str, background: str) -> float:
        def luminance(color: str) -> float:
            channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
            linear = [
                channel / 12.92
                if channel <= 0.04045
                else ((channel + 0.055) / 1.055) ** 2.4
                for channel in channels
            ]
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

        lighter, darker = sorted(
            (luminance(foreground), luminance(background)),
            reverse=True,
        )
        return (lighter + 0.05) / (darker + 0.05)

    def test_eleven_unity_themes_and_retro_are_available(self) -> None:
        self.assertEqual(len(THEME_LABELS), 12)
        self.assertEqual(set(THEME_LABELS), set(THEME_PALETTES))

    def test_defaults_follow_game_mode(self) -> None:
        self.assertEqual(default_theme_for_mode("unity"), UNITY_STANDARD_THEME)
        self.assertEqual(default_theme_for_mode("retro"), UNITY_STANDARD_THEME)

    def test_settings_offer_every_theme_in_both_game_modes(self) -> None:
        expected = tuple(THEME_LABELS)
        self.assertEqual(theme_ids_for_mode("unity"), expected)
        self.assertEqual(theme_ids_for_mode("retro"), expected)
        self.assertIn(RETRO_THEME, theme_ids_for_mode("unity"))
        self.assertIn(UNITY_STANDARD_THEME, theme_ids_for_mode("retro"))

    def test_legacy_and_removed_themes_are_migrated(self) -> None:
        self.assertEqual(normalize_theme("dwm-dark", "unity"), UNITY_STANDARD_THEME)
        self.assertEqual(normalize_theme("arc", "retro"), UNITY_STANDARD_THEME)

    def test_next_attention_button_colors_remain_readable_in_every_theme(self) -> None:
        for theme_id, palette in THEME_PALETTES.items():
            with self.subTest(theme=theme_id, state="alert"):
                self.assertGreaterEqual(
                    self._contrast_ratio(palette["on_attention"], palette["attention"]),
                    4.5,
                )
            with self.subTest(theme=theme_id, state="disabled"):
                self.assertGreaterEqual(
                    self._contrast_ratio(palette["on_dark"], palette["bg3"]),
                    4.5,
                )
