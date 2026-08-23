from __future__ import annotations

import os
import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from dwm.models import GameWindow
from dwm.services.attention_state import WindowAttentionState

if os.name != "nt":
    hotkeys_stub = types.ModuleType("dwm.services.hotkeys_win")
    hotkeys_stub.HotkeyManager = object
    hotkeys_stub.parse_hotkey = lambda _text: (0, 0)
    sys.modules[hotkeys_stub.__name__] = hotkeys_stub

from dwm.app import WindowManagerApp  # noqa: E402


class AppOrderSyncTests(unittest.TestCase):
    def make_app(self) -> WindowManagerApp:
        app = WindowManagerApp.__new__(WindowManagerApp)
        app._all_windows = {
            101: GameWindow(101, "Nealla - Pandawa - Dofus", "Nealla", "Pandawa"),
            102: GameWindow(102, "Nat - Eniripsa - Dofus", "Nat", "Eniripsa"),
            103: GameWindow(103, "Eramis - Féca - Dofus", "Eramis", "Féca"),
        }
        app._managed_order = [101, 102, 103]
        app._streamdeck_order = [101, 102, 103]
        app._ignored = set()
        app._active_game_hwnd = 102
        app.rotation_index = 1
        app.aliases = {}
        app.attention_state = WindowAttentionState()
        app.game_mode = "unity"
        app._scan_revision = 4
        app._attention_blink_phase = True
        app.settings = SimpleNamespace(
            theme="standard",
            language="fr",
            show_character_portraits=True,
            show_character_badges=True,
            attention_blink_enabled=True,
            attention_blink_phase=True,
            character_visuals={},
        )
        app.overlay_ui = Mock()
        app.streamdeck_bridge = Mock()
        app._streamdeck_preview_entries = []
        app._refresh_streamdeck_preview = Mock()
        app.update_listboxes = Mock()
        app._selected_managed_hwnd = Mock(return_value=102)
        return app

    def assert_published_order(self, app: WindowManagerApp, expected: list[int]) -> None:
        self.assertEqual(app._managed_order, expected)
        self.assertEqual(app._streamdeck_order, expected)
        overlay_entries = app.overlay_ui.update_characters.call_args.args[0]
        self.assertEqual([entry.hwnd for entry in overlay_entries], expected)
        snapshot = app.streamdeck_bridge.update_snapshot.call_args.args[0]
        self.assertEqual([entry["hwnd"] for entry in snapshot["windows"]], expected)
        app.update_listboxes.assert_called_once_with(publish_consumers=False)

    def test_app_reorder_is_published_before_the_main_table_rebuild(self) -> None:
        app = self.make_app()

        with patch("dwm.app.get_foreground_hwnd", return_value=102):
            app.move_selected(-1)

        self.assert_published_order(app, [102, 101, 103])

    def test_app_drag_reorder_publishes_the_same_order_to_every_consumer(self) -> None:
        app = self.make_app()
        app.managed_tree = Mock()
        app.managed_tree.get_children.return_value = ("101", "102", "103")
        app._log = Mock()

        with patch("dwm.app.get_foreground_hwnd", return_value=102):
            app._move_managed_window(103, 101, after=False)

        self.assert_published_order(app, [103, 101, 102])


if __name__ == "__main__":
    unittest.main()
