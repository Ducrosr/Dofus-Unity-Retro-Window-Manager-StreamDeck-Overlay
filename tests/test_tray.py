from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from tests import test_app_order_sync
from dwm.services.tray import TrayController, TrayState
from dwm.storage.profiles import Profile, save_profile
from dwm.storage.settings import Settings


class TrayTests(unittest.TestCase):
    def test_real_menu_dynamic_items_checks_and_callback_bindings(self):
        # Isolate the non-graphical backend so other tests retain their native backend.
        script = '''
import pystray
from dwm.services.tray import TrayController, TrayState
from dwm.services.i18n import set_language
calls = []
tray = TrayController("unused.ico")
tray.set_state(TrayState(profiles=("Alpha", "Beta"), active_profile="Beta", game_mode="retro", overlay_enabled=True))
menu = tray._build_menu(pystray, show=lambda: calls.append("show"), refresh=lambda: None,
    quit_app=lambda: None, toggle_hotkeys=lambda: calls.append("hotkeys"),
    select_profile=lambda name: calls.append(name), select_mode=lambda mode: calls.append(mode),
    toggle_overlay=lambda: calls.append("overlay"))
items = tuple(menu)
profiles = tuple(items[1].submenu)
assert [item.text for item in profiles] == ["Alpha", "Beta"]
assert [item.checked for item in profiles] == [False, True]
profiles[0](None); profiles[1](None)
modes = tuple(items[2].submenu)
assert [item.checked for item in modes] == [False, True]
modes[0](None); modes[1](None); items[3](None)
assert calls == ["Alpha", "Beta", "unity", "retro", "overlay"]
assert items[3].checked is True
tray.set_state(TrayState(profiles=("Gamma",), hotkeys_paused=True, enabled=False))
assert [item.text for item in items[1].submenu] == ["Gamma"]
assert items[1].enabled is False and items[2].enabled is False and items[3].enabled is False
assert items[5].text == "Reprendre les raccourcis"
set_language("en")
assert items[5].text == "Resume shortcuts"
tray.set_state(TrayState())
assert items[1].enabled is False
'''
        result = subprocess.run([sys.executable, "-c", script],
                                env={**os.environ, "PYSTRAY_BACKEND": "dummy"},
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_menu_refresh_only_when_snapshot_changes(self):
        tray = TrayController("unused.ico")
        tray._icon = Mock()
        state = TrayState(profiles=("Alpha",), active_profile="Alpha")
        tray.set_state(state)
        tray.set_state(state)
        tray._icon.update_menu.assert_called_once()
        tray.set_state(TrayState(language="en"))
        self.assertEqual(tray._icon.update_menu.call_count, 2)

    def make_app(self):
        app = test_app_order_sync.AppOrderSyncTests().make_app()
        app.root = Mock()
        app.root.grab_current.return_value = None
        app._sync_tray_state = Mock()
        app.switch_game_mode = Mock()
        app.selected_profile = Mock()
        app.load_profile_selected = Mock()
        app.toggle_rotation_overlay = Mock()
        app.toggle_hotkeys_paused = Mock()
        app._show_main_window = Mock()
        app._refresh_profile_combo = Mock()
        app.on_close = Mock()
        return app

    def test_profile_action_switches_mode_before_using_existing_loader(self):
        app = self.make_app()
        actions = []
        app.switch_game_mode.side_effect = lambda value: actions.append(("mode", value))
        app.selected_profile.set.side_effect = lambda value: actions.append(("profile", value))
        app.load_profile_selected.side_effect = lambda: actions.append(("load",))
        with tempfile.TemporaryDirectory() as directory:
            app.dirs = {"profiles": Path(directory)}
            save_profile(Path(directory), Profile("Retro team", [], {}, "", "", game_mode="retro"))
            app._handle_tray_action("profile", "Retro team")
        self.assertEqual(actions, [("mode", "retro"), ("profile", "Retro team"), ("load",)])

    def test_modal_dialog_blocks_queued_changes(self):
        app = self.make_app()
        app.root.grab_current.return_value = object()
        for action, value in [("mode", "retro"), ("profile", "Missing"), ("overlay", ""), ("hotkeys", "")]:
            app._handle_tray_action(action, value)
        app.switch_game_mode.assert_not_called()
        app.load_profile_selected.assert_not_called()
        app.toggle_rotation_overlay.assert_not_called()
        app.toggle_hotkeys_paused.assert_not_called()

    def test_toggles_use_existing_actions_and_quit_does_not_touch_destroyed_ui(self):
        app = self.make_app()
        app._handle_tray_action("overlay")
        app._handle_tray_action("hotkeys")
        app._handle_tray_action("mode", "invalid")
        app.toggle_rotation_overlay.assert_called_once()
        app.toggle_hotkeys_paused.assert_called_once()
        app.switch_game_mode.assert_not_called()
        app._sync_tray_state.reset_mock()
        app._handle_tray_action("quit")
        app.on_close.assert_called_once_with(force=True)
        app._sync_tray_state.assert_not_called()

    def test_deleted_profile_does_not_change_selection_or_mode(self):
        app = self.make_app()
        with tempfile.TemporaryDirectory() as directory, patch("dwm.app.messagebox.showerror") as error:
            app.dirs = {"profiles": Path(directory)}
            app._handle_tray_action("profile", "Deleted")
        error.assert_called_once()
        app.selected_profile.set.assert_not_called()
        app.switch_game_mode.assert_not_called()
        app._refresh_profile_combo.assert_called_once()

    def test_snapshot_uses_active_profile_and_cached_names_without_reading_disk(self):
        app = self.make_app()
        app.tray = Mock()
        app.settings = Settings(rotation_overlay_enabled=True)
        app._hotkeys_paused = True
        app._active_profile_name = "Loaded"
        app._tray_profile_names = ("Loaded", "Other")
        app._get_profiles = Mock(side_effect=AssertionError("unexpected disk scan"))
        test_app_order_sync.WindowManagerApp._sync_tray_state(app)
        state = app.tray.set_state.call_args.args[0]
        self.assertEqual(state.active_profile, "Loaded")
        self.assertEqual(state.profiles, ("Loaded", "Other"))
        self.assertTrue(state.overlay_enabled and state.hotkeys_paused and state.enabled)


if __name__ == "__main__":
    unittest.main()
