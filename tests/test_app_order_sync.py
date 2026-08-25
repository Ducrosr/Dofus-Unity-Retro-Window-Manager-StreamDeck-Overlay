from __future__ import annotations

import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from dwm.models import GameWindow
from dwm.services.attention_state import WindowAttentionState
from dwm.storage.profiles import Profile, save_profile

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

    def test_direct_position_focus_uses_current_managed_order(self) -> None:
        app = self.make_app()
        app._focus_from_auxiliary_display = Mock()
        app._log = Mock()

        self.assertTrue(app.focus_managed_position(3))
        self.assertEqual(app.rotation_index, 2)
        app._focus_from_auxiliary_display.assert_called_once_with(103)
        self.assertFalse(app.focus_managed_position(9))

    def test_only_configured_direct_hotkeys_are_registered(self) -> None:
        app = self.make_app()
        app.hotkeys = Mock()
        app.root = SimpleNamespace(after=lambda _delay, callback: callback())
        app._log = Mock()
        app.focus_managed_position = Mock(return_value=True)
        app.settings.hotkeys = {
            "forward": "F5",
            "backward": "F6",
            "ignore": "F7",
            "next_attention": "F8",
            "refresh": "Ctrl+Alt+R",
            "window_1": "1",
            "window_2": "",
            "window_3": "3",
        }
        app.request_rotation = Mock()
        app.ignore_selected = Mock()
        app.focus_next_attention = Mock()
        app.refresh_windows = Mock()

        app._register_hotkeys()

        registered_ids = [call.args[0] for call in app.hotkeys.set_hotkey.call_args_list]
        self.assertEqual(registered_ids, [1, 2, 3, 4, 5, 101, 103])
        self.assertEqual(
            [call.args[0] for call in app.hotkeys.clear_hotkey.call_args_list],
            list(range(101, 109)),
        )
        direct_callback = next(
            call.args[2]
            for call in app.hotkeys.set_hotkey.call_args_list
            if call.args[0] == 103
        )
        direct_callback()
        app.focus_managed_position.assert_called_once_with(3)

    def test_profiles_can_customize_the_same_character_differently(self) -> None:
        app = WindowManagerApp.__new__(WindowManagerApp)
        app.aliases = {}
        app._legacy_character_visuals = {}
        app.character_visuals = {}
        app.game_mode = "unity"
        first = Profile(
            "Serveur A",
            ["Nealla"],
            {"Nealla": "Terre"},
            "",
            "",
            visuals={"Nealla": {"portrait": "", "badge": "ankama_force"}},
        )
        second = Profile(
            "Serveur B",
            ["Nealla"],
            {"Nealla": "Eau"},
            "",
            "",
            visuals={"Nealla": {"portrait": "", "badge": "ankama_chance"}},
        )

        app._apply_loaded_profile(first, migrate_legacy=False)
        self.assertEqual(app.aliases["Nealla"], "Terre")
        self.assertEqual(app.character_visuals["Nealla"]["badge"], "ankama_force")
        app._apply_loaded_profile(second, migrate_legacy=False)
        self.assertEqual(app.aliases["Nealla"], "Eau")
        self.assertEqual(app.character_visuals["Nealla"]["badge"], "ankama_chance")

    def test_smart_loading_applies_one_exact_same_mode_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profiles_dir = Path(tmp)
            save_profile(
                profiles_dir,
                Profile(
                    "Jiva",
                    ["Eramis", "Nealla", "Nat"],
                    {"Nealla": "Terre"},
                    "",
                    "",
                    visuals={},
                    game_mode="unity",
                ),
            )
            app = self.make_app()
            app.settings.smart_profile_loading_enabled = True
            app.settings.last_profile = ""
            app._active_profile_name = ""
            app._profile_match_signature = None
            app._legacy_character_visuals = {}
            app.character_visuals = {}
            app.desired_order_pseudos = []
            app.dirs = {"profiles": profiles_dir}
            app.settings_path = profiles_dir / "settings.json"
            app.selected_profile = Mock()
            app._log = Mock()

            with patch("dwm.app.save_settings"):
                app._maybe_auto_load_profile()

        self.assertEqual(app._active_profile_name, "Jiva")
        self.assertEqual(app.aliases, {"Nealla": "Terre"})
        app.selected_profile.set.assert_called_once_with("Jiva")

    def test_smart_loading_refuses_ambiguous_exact_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profiles_dir = Path(tmp)
            for name in ("Serveur A", "Serveur B"):
                save_profile(
                    profiles_dir,
                    Profile(
                        name,
                        ["Nealla", "Nat", "Eramis"],
                        {},
                        "",
                        "",
                        visuals={},
                        game_mode="unity",
                    ),
                )
            app = self.make_app()
            app.settings.smart_profile_loading_enabled = True
            app._active_profile_name = ""
            app._profile_match_signature = None
            app.dirs = {"profiles": profiles_dir}
            app.selected_profile = Mock()
            app._log = Mock()

            app._maybe_auto_load_profile()

        self.assertEqual(app._active_profile_name, "")
        app.selected_profile.set.assert_not_called()
        self.assertIn("Sélection manuelle requise", app._log.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
