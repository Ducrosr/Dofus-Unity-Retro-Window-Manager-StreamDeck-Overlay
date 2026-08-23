from __future__ import annotations

import unittest

from dwm.services.window_order import (
    align_streamdeck_slots_with_managed,
    move_column,
    move_window,
    move_window_by_delta,
    move_window_to_index,
)


class WindowOrderTests(unittest.TestCase):
    def test_drag_can_reorder_columns(self) -> None:
        self.assertEqual(
            move_column(["class", "name", "alias", "hwnd"], "alias", "class"),
            ["alias", "class", "name", "hwnd"],
        )

    def test_drag_can_move_a_window_before_another(self) -> None:
        self.assertEqual(move_window([101, 102, 103, 104], 104, 102), [101, 104, 102, 103])

    def test_drag_can_move_a_window_after_another(self) -> None:
        self.assertEqual(move_window([101, 102, 103, 104], 101, 103, after=True), [102, 103, 101, 104])

    def test_streamdeck_buttons_can_move_a_window_up_or_down(self) -> None:
        self.assertEqual(move_window_by_delta([101, 102, 103], 102, -1), [102, 101, 103])
        self.assertEqual(move_window_by_delta([101, 102, 103], 102, 1), [101, 103, 102])

    def test_streamdeck_buttons_do_not_wrap_at_the_edges(self) -> None:
        self.assertEqual(move_window_by_delta([101, 102, 103], 101, -1), [101, 102, 103])
        self.assertEqual(move_window_by_delta([101, 102, 103], 103, 1), [101, 102, 103])

    def test_overlay_drag_moves_a_window_to_an_exact_index(self) -> None:
        self.assertEqual(move_window_to_index([101, 102, 103, 104], 104, 1), [101, 104, 102, 103])
        self.assertEqual(move_window_to_index([101, 102, 103, 104], 101, 99), [102, 103, 104, 101])

    def test_streamdeck_follows_managed_order_while_ignored_slot_stays_anchored(self) -> None:
        actual = align_streamdeck_slots_with_managed(
            [101, 102, 103, 104],
            [103, 101, 104],
            {102},
        )

        self.assertEqual(actual, [103, 102, 101, 104])

    def test_unignored_window_can_follow_its_new_managed_position(self) -> None:
        actual = align_streamdeck_slots_with_managed(
            [103, 102, 101, 104],
            [103, 101, 104, 102],
            set(),
        )

        self.assertEqual(actual, [103, 101, 104, 102])


if __name__ == "__main__":
    unittest.main()
