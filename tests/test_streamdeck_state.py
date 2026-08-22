from __future__ import annotations

import unittest

from dwm.models import GameWindow
from dwm.services.streamdeck_state import build_streamdeck_windows, reconcile_streamdeck_order


class StreamDeckStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.windows = {
            101: GameWindow(101, "Nealla - Pandawa - Dofus", "Nealla", "Pandawa"),
            102: GameWindow(102, "Nat - Eniripsa - Dofus", "Nat", "Eniripsa"),
            103: GameWindow(103, "Eramis - Féca - Dofus", "Eramis", "Féca"),
        }

    def test_ignored_window_keeps_its_stable_streamdeck_slot(self) -> None:
        order = reconcile_streamdeck_order([101, 102, 103], self.windows, [101, 103])

        self.assertEqual(order, [101, 102, 103])

    def test_snapshot_includes_ignored_windows_but_excludes_them_from_rotation_positions(self) -> None:
        entries = build_streamdeck_windows(
            self.windows,
            [101, 102, 103],
            [101, 103],
            {102},
            {"Nealla": "Panda"},
            102,
        )

        self.assertEqual([entry["hwnd"] for entry in entries], [101, 102, 103])
        self.assertEqual(entries[1]["slot"], 2)
        self.assertIsNone(entries[1]["position"])
        self.assertTrue(entries[1]["ignored"])
        self.assertTrue(entries[1]["active"])
        self.assertEqual(entries[0]["position"], 1)
        self.assertEqual(entries[2]["position"], 2)
        self.assertEqual(entries[0]["name"], "Nealla")
        self.assertEqual(entries[0]["alias"], "Panda")

    def test_blank_alias_is_published_as_blank_and_never_as_the_name(self) -> None:
        entries = build_streamdeck_windows(
            self.windows,
            [101],
            [101],
            set(),
            {"Nealla": ""},
            None,
        )

        self.assertEqual(entries[0]["alias"], "")
        self.assertEqual(entries[0]["name"], "Nealla")


if __name__ == "__main__":
    unittest.main()
