from __future__ import annotations

import threading
import unittest
from unittest.mock import Mock, patch

from tests import test_app_order_sync
from dwm.models import GameWindow
from dwm.services.character_roster import CharacterRoster
from dwm.storage.profiles import Profile


class CharacterLifecycleTests(unittest.TestCase):
    def make_app(self):
        app = test_app_order_sync.AppOrderSyncTests().make_app()
        app._roster = CharacterRoster(order=["Nealla", "Nat", "Eramis"], slots=["Nealla", "Nat", "Eramis"])
        app._saved_profile_order = list(app._roster.order)
        app.settings.fixed_character_slots = True
        app.settings.smart_profile_loading_enabled = False
        app.settings.hotkey_scope = "game"
        app.settings.refresh_seconds = 10
        app._windows_sig = ()
        app._privilege_mismatch_suspected = False
        app._stop_event = threading.Event()
        app._log = Mock()
        app.last_update_time = Mock()
        app._schedule_smart_profile_match = Mock()
        app._update_popup_watcher_targets = Mock()
        app._request_ui_update = Mock()
        app.hotkeys = Mock()
        app.update_listboxes = lambda **_kwargs: app._publish_order_consumers()
        return app

    @patch("dwm.app.suspect_privilege_mismatch", return_value=False)
    @patch("dwm.app.get_foreground_hwnd", return_value=101)
    def test_scan_reconnect_restores_ignored_state_without_shifting_slots(self, *_mocks):
        app = self.make_app()
        app._selected_managed_hwnd = Mock(return_value=102)
        app.ignore_selected()
        app._apply_windows([app._all_windows[101], app._all_windows[103]])
        snapshot = app.streamdeck_bridge.update_snapshot.call_args.args[0]
        self.assertEqual([entry["hwnd"] for entry in snapshot["windows"]], [101, -2, 103])
        self.assertFalse(app.focus_managed_position(2))
        app._apply_windows([*app._all_windows.values(), GameWindow(999, "Nat - Dofus", "Nat", "Eniripsa")])
        self.assertEqual(app._ignored, {999})
        self.assertEqual(app._managed_order, [101, 103])
        self.assertEqual(app._streamdeck_order, [101, 999, 103])
        app.hotkeys.set_context.assert_called_with(enabled=True, allowed_hwnds=frozenset({101, 999, 103}))
        app._selected_ignored_hwnd = Mock(return_value=999)
        app.unignore_selected()
        self.assertEqual(app._managed_order, [101, 999, 103])

    @patch("dwm.app.suspect_privilege_mismatch", return_value=False)
    @patch("dwm.app.get_foreground_hwnd", return_value=101)
    def test_reorder_survives_scan_and_undo_survives_new_handle(self, *_mocks):
        app = self.make_app()
        app.move_selected(-1)
        self.assertEqual(app._managed_order, [102, 101, 103])
        app._apply_windows(list(app._all_windows.values()))
        self.assertEqual(app._managed_order, [102, 101, 103])
        app._apply_windows([app._all_windows[101], app._all_windows[103]])
        app._apply_windows([*app._all_windows.values(), GameWindow(999, "Nat - Dofus", "Nat", "Eniripsa")])
        self.assertEqual(app._managed_order, [999, 101, 103])
        app.undo_order_change()
        self.assertEqual(app._managed_order, [101, 999, 103])
        self.assertEqual(app._streamdeck_order, [101, 999, 103])

    @patch("dwm.app.get_foreground_hwnd", return_value=101)
    @patch("dwm.app.is_window", return_value=True)
    @patch("dwm.app.get_class_name", return_value="UnityWndClass")
    @patch("dwm.app.get_window_title", return_value="Nat - Eniripsa - Dofus 3.0")
    def test_event_reconnect_uses_same_roster_as_scans(self, *_mocks):
        app = self.make_app()
        app._selected_managed_hwnd = Mock(return_value=102)
        app.ignore_selected()
        app._apply_win_event("destroy", 102)
        app._apply_win_event("create", 999)
        self.assertIn(999, app._ignored)
        self.assertNotIn(999, app._managed_order)
        self.assertEqual(app._roster.bindings(app._all_windows), [101, 999, 103])

    @patch("dwm.app.suspect_privilege_mismatch", return_value=False)
    @patch("dwm.app.get_foreground_hwnd", return_value=101)
    def test_reused_handle_does_not_inherit_previous_characters_ignored_state(self, *_mocks):
        app = self.make_app()
        app._selected_managed_hwnd = Mock(return_value=102)
        app.ignore_selected()
        app._apply_windows([app._all_windows[101], GameWindow(102, "Autre - Dofus", "Autre", ""), app._all_windows[103]])
        self.assertNotIn(102, app._ignored)
        self.assertEqual(app._roster.bindings(app._all_windows), [101, -2, 103, 102])

    @patch("dwm.app.get_foreground_hwnd", return_value=101)
    def test_switching_profile_resets_slots_ignored_state_and_undo_history(self, *_mocks):
        app = self.make_app()
        app._roster.ignored = {"nat"}
        app._roster.checkpoint()
        app._activate_profile(Profile("Serveur B", ["Eramis", "Nat", "Nealla"], {}, "", "", visuals={}), migrate_legacy=False)
        self.assertEqual(app._managed_order, [103, 102, 101])
        self.assertEqual(app._streamdeck_order, [103, 102, 101])
        self.assertEqual(app._ignored, set())
        self.assertEqual(app._roster.history, [])

    def test_failed_direct_focus_keeps_the_previous_rotation(self):
        app = self.make_app()
        app._focus_from_auxiliary_display = Mock(return_value=False)
        self.assertFalse(app.focus_managed_position(3))
        self.assertEqual(app.rotation_index, 1)

    def test_stale_streamdeck_command_cannot_target_another_profile_or_name(self):
        app = self.make_app()
        app._active_profile_name = "Serveur B"
        app._focus_hwnd_measured = Mock()
        result = app._execute_streamdeck_command("focus", {"hwnd": 101, "profile": "Serveur A"})
        self.assertFalse(result["ok"])
        result = app._execute_streamdeck_command("focus", {"hwnd": 101, "pseudo": "Nat"})
        self.assertFalse(result["ok"])
        app._focus_hwnd_measured.assert_not_called()
