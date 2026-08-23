from __future__ import annotations

import unittest

from dwm.models import GameWindow
from dwm.services.display_overlay import (
    DEFAULT_ROTATION_OVERLAY_LAYOUT,
    build_rotation_displays,
    build_single_display,
    calculate_overlay_text_scale,
    clamp_notification_duration,
    clamp_overlay_opacity,
    compose_overlay_row,
    format_tk_geometry,
    normalize_overlay_anchor,
    normalize_overlay_layout,
    place_inside_rect,
)


class DisplayOverlayTests(unittest.TestCase):
    def test_rotation_display_keeps_alias_and_active_character(self) -> None:
        windows = {
            10: GameWindow(10, "Nealla - Dofus", "Nealla", "Pandawa"),
            20: GameWindow(20, "Nat - Dofus", "Nat", "Eniripsa"),
        }

        rows = build_rotation_displays(windows, [20, 999, 10], {"Nealla": "Terre"}, 10)

        self.assertEqual([row.hwnd for row in rows], [20, 10])
        self.assertEqual([row.position for row in rows], [1, 2])
        self.assertEqual(rows[1].primary_text, "Terre")
        self.assertEqual(rows[1].secondary_text, "Nealla · Pandawa")
        self.assertTrue(rows[1].active)

    def test_ignored_character_is_described_as_outside_rotation(self) -> None:
        window = GameWindow(30, "Syra - Dofus", "Syra", "Cra")

        row = build_single_display(window, aliases={}, managed_order=[10, 20], active=True)

        self.assertIsNone(row.position)
        self.assertEqual(row.position_text, "Hors rotation")

    def test_overlay_position_uses_the_selected_game_window_corner(self) -> None:
        rect = (100, 200, 1100, 900)

        self.assertEqual(place_inside_rect(rect, (300, 80), "top_left"), (128, 228))
        self.assertEqual(place_inside_rect(rect, (300, 80), "top_center"), (450, 228))
        self.assertEqual(place_inside_rect(rect, (300, 80), "bottom_right"), (772, 792))

    def test_overlay_preferences_are_normalized(self) -> None:
        self.assertEqual(normalize_overlay_anchor("unknown"), "top_center")
        self.assertEqual(clamp_overlay_opacity(10), 35)
        self.assertEqual(clamp_overlay_opacity(120), 100)
        self.assertEqual(clamp_notification_duration(100), 600)
        self.assertEqual(clamp_notification_duration(9000), 5000)
        self.assertEqual(format_tk_geometry(320, 90, -25, 40), "320x90-25+40")

    def test_default_overlay_layout_matches_requested_two_line_design(self) -> None:
        window = GameWindow(40, "Nealla - Dofus", "Nealla", "Pandawa")
        entry = build_single_display(
            window,
            aliases={"Nealla": "Terre"},
            managed_order=[40],
            active=True,
        )

        self.assertEqual(
            compose_overlay_row(entry, DEFAULT_ROTATION_OVERLAY_LAYOUT),
            ("1", "Nealla", "Pandawa · Terre"),
        )

    def test_overlay_layout_can_hide_and_reorder_fields(self) -> None:
        window = GameWindow(50, "Nat - Dofus", "Nat", "Eniripsa")
        entry = build_single_display(
            window,
            aliases={},
            managed_order=[50],
            active=False,
        )
        layout = {
            "left": "class",
            "line1": "alias",
            "line2_left": "none",
            "line2_right": "name",
        }

        self.assertEqual(compose_overlay_row(entry, layout), ("Eniripsa", "—", "Nat"))
        self.assertEqual(
            normalize_overlay_layout({"left": "invalid"}),
            DEFAULT_ROTATION_OVERLAY_LAYOUT,
        )

    def test_attention_and_character_appearance_are_propagated(self) -> None:
        window = GameWindow(60, "Nealla - Dofus", "Nealla", "Pandawa")

        rows = build_rotation_displays(
            {60: window},
            [60],
            {},
            None,
            {60},
            {"Nealla": {"portrait": "portrait-data", "badge": "ankama_force"}},
        )

        self.assertTrue(rows[0].attention)
        self.assertEqual(rows[0].portrait_data, "portrait-data")
        self.assertEqual(rows[0].badge, "ankama_force")

    def test_attention_queue_order_is_exposed_independently_from_rotation_order(self) -> None:
        windows = {
            10: GameWindow(10, "A - Dofus", "A", "Cra"),
            20: GameWindow(20, "B - Dofus", "B", "Féca"),
        }

        rows = build_rotation_displays(windows, [10, 20], {}, None, [20, 10])

        self.assertEqual([row.attention_order for row in rows], [2, 1])

    def test_overlay_text_scales_with_width_and_available_row_height(self) -> None:
        self.assertEqual(
            calculate_overlay_text_scale(300, 208, 4, locked=False, fixed_height=True),
            1.0,
        )
        self.assertEqual(
            calculate_overlay_text_scale(600, 392, 4, locked=False, fixed_height=True),
            2.0,
        )
        self.assertEqual(
            calculate_overlay_text_scale(240, 90, 8, locked=False, fixed_height=True),
            0.55,
        )


if __name__ == "__main__":
    unittest.main()
