from __future__ import annotations

import unittest

from dwm.models import GameWindow
from dwm.services.window_table import window_table_values


class WindowTableTests(unittest.TestCase):
    def test_class_name_alias_and_hwnd_have_independent_columns(self) -> None:
        window = GameWindow(
            hwnd=104,
            title="Nealla - Pandawa - Dofus",
            pseudo="Nealla",
            character_class="Pandawa",
        )

        self.assertEqual(
            window_table_values(window, "Panda"),
            ("Pandawa", "Nealla", "Panda", "104"),
        )


if __name__ == "__main__":
    unittest.main()
