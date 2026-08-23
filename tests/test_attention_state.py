from __future__ import annotations

import unittest

from dwm.services.attention_state import WindowAttentionState


class AttentionStateTests(unittest.TestCase):
    def test_only_known_inactive_windows_can_request_attention(self) -> None:
        state = WindowAttentionState()

        self.assertFalse(state.mark(0, {10, 20}))
        self.assertFalse(state.mark(30, {10, 20}))
        self.assertFalse(state.mark(10, {10, 20}, active_hwnd=10))
        self.assertTrue(state.mark(20, {10, 20}, active_hwnd=10))
        self.assertFalse(state.mark(20, {10, 20}, active_hwnd=10))
        self.assertEqual(state.snapshot(), {20})

    def test_focus_and_window_removal_clear_attention(self) -> None:
        state = WindowAttentionState()
        state.mark(10, {10, 20})
        state.mark(20, {10, 20})

        self.assertTrue(state.clear(10))
        self.assertTrue(state.discard_unknown({10}))
        self.assertEqual(state.snapshot(), set())

    def test_queue_keeps_first_request_order_without_reordering_duplicates(self) -> None:
        state = WindowAttentionState()

        state.mark(20, {10, 20, 30})
        state.mark(10, {10, 20, 30})
        state.mark(20, {10, 20, 30})
        state.mark(30, {10, 20, 30})

        self.assertEqual(state.queue(), (20, 10, 30))
        self.assertEqual(state.next(), 20)
        self.assertEqual(state.rank(10), 2)
        self.assertIsNone(state.rank(99))

    def test_discard_unknown_preserves_remaining_queue_order(self) -> None:
        state = WindowAttentionState()
        for hwnd in (30, 10, 20):
            state.mark(hwnd, {10, 20, 30})

        self.assertTrue(state.discard_unknown({10, 30}))
        self.assertEqual(state.queue(), (30, 10))


if __name__ == "__main__":
    unittest.main()
