from __future__ import annotations

import unittest

from dwm.services.game_mode import game_mode_label, normalize_game_mode, win_event_filter


class GameModeTests(unittest.TestCase):
    def test_mode_normalization_and_labels(self) -> None:
        self.assertEqual(normalize_game_mode(" RETRO "), "retro")
        self.assertEqual(normalize_game_mode("inconnu"), "unity")
        self.assertEqual(game_mode_label("unity"), "Unity")
        self.assertEqual(game_mode_label("retro"), "Retro")

    def test_unity_event_filter(self) -> None:
        self.assertEqual(win_event_filter("unity", "ignored"), (("UnityWndClass",), None))

    def test_retro_event_filter_normalizes_keyword(self) -> None:
        self.assertEqual(
            win_event_filter("retro", " DOFUS RETRO V "),
            (("Chrome_WidgetWin_1",), {"Chrome_WidgetWin_1": "dofus retro v"}),
        )


if __name__ == "__main__":
    unittest.main()
