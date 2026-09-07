from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dwm.services.hotkey_context import context_allows_hotkeys


class HotkeyContextTests(unittest.TestCase):
    def test_global_game_and_pause_rules(self):
        self.assertTrue(context_allows_hotkeys(True, None, 900))
        self.assertFalse(context_allows_hotkeys(False, None, 100))
        self.assertFalse(context_allows_hotkeys(True, frozenset(), 100))
        self.assertFalse(context_allows_hotkeys(True, frozenset({100}), 900))
        self.assertTrue(context_allows_hotkeys(True, frozenset({100}), 100))

    def load_manager(self):
        # Exercise the real manager on every OS, replacing only the native API.
        path = Path(__file__).resolve().parents[1] / "dwm/services/hotkeys_win.py"
        spec = importlib.util.spec_from_file_location("dwm.services._hotkeys_under_test", path)
        module = importlib.util.module_from_spec(spec)
        user32 = Mock()
        user32.GetForegroundWindow.return_value = 100
        user32.RegisterHotKey.return_value = True
        with patch("os.name", "nt"), patch("ctypes.WinDLL", side_effect=[user32, Mock()], create=True):
            spec.loader.exec_module(module)
        manager = module.HotkeyManager()
        manager._ready.set()
        return manager, user32

    def test_leaving_game_unregisters_keys_and_returning_registers_them(self):
        manager, native = self.load_manager()
        manager.set_hotkey(101, "1", lambda: None)
        manager.set_context(enabled=True, allowed_hwnds=frozenset({100}))
        manager._sync_context()
        self.assertEqual(native.RegisterHotKey.call_count, 1)
        native.UnregisterHotKey.reset_mock()
        native.GetForegroundWindow.return_value = 900
        manager._sync_context()
        native.UnregisterHotKey.assert_called_once_with(None, 101)
        manager._sync_context()
        self.assertEqual(native.UnregisterHotKey.call_count, 1)
        native.GetForegroundWindow.return_value = 100
        manager._sync_context()
        self.assertEqual(native.RegisterHotKey.call_count, 2)

    def test_paused_configuration_does_not_register_replaced_shortcuts(self):
        manager, native = self.load_manager()
        manager.set_context(enabled=False)
        manager.set_hotkey(101, "1", lambda: None)
        manager._apply_registration(101)
        native.RegisterHotKey.assert_not_called()
        manager.set_hotkey(101, "2", lambda: None)
        manager.set_context(enabled=True)
        manager._sync_context()
        self.assertEqual(native.RegisterHotKey.call_args.args[-1], ord("2"))

    def test_removing_last_game_releases_shortcuts(self):
        manager, native = self.load_manager()
        manager.set_hotkey(1, "F5", lambda: None)
        manager.set_context(enabled=True, allowed_hwnds=frozenset({100}))
        manager._sync_context()
        native.UnregisterHotKey.reset_mock()
        manager.set_context(enabled=True, allowed_hwnds=frozenset())
        manager._sync_context()
        native.UnregisterHotKey.assert_called_once_with(None, 1)
