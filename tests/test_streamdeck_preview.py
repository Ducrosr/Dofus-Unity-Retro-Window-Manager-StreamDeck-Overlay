from __future__ import annotations

import unittest

from dwm.services.streamdeck_preview import STREAMDECK_PROFILE_LAYOUT, format_character_key


class StreamDeckPreviewTests(unittest.TestCase):
    def test_default_profile_has_fifteen_keys_and_eight_character_slots(self) -> None:
        self.assertEqual(len(STREAMDECK_PROFILE_LAYOUT), 3)
        self.assertTrue(all(len(row) == 5 for row in STREAMDECK_PROFILE_LAYOUT))
        self.assertEqual(
            [key for row in STREAMDECK_PROFILE_LAYOUT for key in row if isinstance(key, int)],
            list(range(1, 9)),
        )

    def test_character_key_uses_the_default_four_line_layout(self) -> None:
        self.assertEqual(
            format_character_key(4, "Nealla", "Pandawa", "Terre"),
            "4\nNealla\nPandawa\nTerre",
        )

    def test_ignored_position_and_blank_alias_use_a_dash(self) -> None:
        self.assertEqual(
            format_character_key(None, "Nealla", "Pandawa", ""),
            "—\nNealla\nPandawa\n—",
        )


if __name__ == "__main__":
    unittest.main()
