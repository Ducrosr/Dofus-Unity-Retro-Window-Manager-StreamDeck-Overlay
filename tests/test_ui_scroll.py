from __future__ import annotations

import unittest

from dwm.services.ui_scroll import vertical_scroll_needed, wheel_scroll_units


class UiScrollTests(unittest.TestCase):
    def test_mouse_wheel_direction_matches_vertical_scrolling(self) -> None:
        self.assertEqual(wheel_scroll_units(120), -1)
        self.assertEqual(wheel_scroll_units(-120), 1)

    def test_high_resolution_or_fast_wheel_values_are_supported(self) -> None:
        self.assertEqual(wheel_scroll_units(30), -1)
        self.assertEqual(wheel_scroll_units(-360), 3)
        self.assertEqual(wheel_scroll_units(0), 0)

    def test_scroll_is_needed_only_when_content_is_clipped(self) -> None:
        self.assertFalse(vertical_scroll_needed(0.0, 1.0))
        self.assertTrue(vertical_scroll_needed(0.0, 0.75))
        self.assertTrue(vertical_scroll_needed(0.1, 1.0))


if __name__ == "__main__":
    unittest.main()
