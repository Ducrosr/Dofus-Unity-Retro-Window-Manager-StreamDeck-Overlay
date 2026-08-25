from __future__ import annotations

import unittest

from dwm.services.display_presets import (
    DISPLAY_PRESET_IDS,
    apply_display_preset,
    display_preset_values,
)
from dwm.storage.settings import Settings


class DisplayPresetTests(unittest.TestCase):
    def test_all_presets_return_independent_layout_copies(self) -> None:
        self.assertEqual(DISPLAY_PRESET_IDS, ("minimal", "balanced", "complete"))
        first = display_preset_values("minimal")
        second = display_preset_values("minimal")
        first["rotation_overlay_layout"]["line1"] = "alias"
        self.assertEqual(second["rotation_overlay_layout"]["line1"], "name")

    def test_minimal_removes_optional_chrome_and_visuals(self) -> None:
        settings = Settings()
        apply_display_preset(settings, "minimal")

        self.assertFalse(settings.rotation_overlay_show_title)
        self.assertFalse(settings.rotation_overlay_show_reorder_buttons)
        self.assertFalse(settings.show_overlay_portraits)
        self.assertFalse(settings.show_popup_badges)
        self.assertEqual(settings.rotation_overlay_layout["line2_left"], "none")

    def test_complete_restores_every_visual_control(self) -> None:
        settings = Settings(
            rotation_overlay_show_title=False,
            rotation_overlay_show_reorder_buttons=False,
            show_popup_portraits=False,
            show_popup_badges=False,
            show_overlay_portraits=False,
            show_overlay_badges=False,
        )
        apply_display_preset(settings, "complete")

        self.assertTrue(settings.rotation_overlay_show_title)
        self.assertTrue(settings.rotation_overlay_show_reorder_buttons)
        self.assertTrue(settings.show_popup_portraits)
        self.assertTrue(settings.show_popup_badges)
        self.assertTrue(settings.show_overlay_portraits)
        self.assertTrue(settings.show_overlay_badges)

    def test_unknown_preset_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            display_preset_values("cinematic")

