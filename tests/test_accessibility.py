from __future__ import annotations

import unittest

from dwm.services.accessibility import (
    clamp_ui_scale_percent,
    high_contrast_palette,
    motion_allowed,
)


class AccessibilityTests(unittest.TestCase):
    def test_ui_scale_is_clamped(self) -> None:
        self.assertEqual(clamp_ui_scale_percent(40), 80)
        self.assertEqual(clamp_ui_scale_percent("125"), 125)
        self.assertEqual(clamp_ui_scale_percent(900), 160)
        self.assertEqual(clamp_ui_scale_percent("invalid"), 100)

    def test_high_contrast_keeps_accent_but_replaces_neutral_colors(self) -> None:
        palette = {"bg": "#123456", "fg": "#aaaaaa", "accent": "#ff8800"}
        result = high_contrast_palette(palette, enabled=True)

        self.assertEqual(result["bg"], "#000000")
        self.assertEqual(result["fg"], "#ffffff")
        self.assertEqual(result["accent"], "#ff8800")

    def test_reduce_motion_disables_animation(self) -> None:
        self.assertFalse(motion_allowed(reduce_motion=True))
        self.assertTrue(motion_allowed(reduce_motion=False))

