from __future__ import annotations

import sys
import unittest
from unittest.mock import Mock, patch

from dwm.services.monitor_layout import Monitor, choose_monitor, list_monitors, overlay_position
from dwm.storage.settings import Settings
from dwm.storage.profiles import Profile


class MonitorLayoutTests(unittest.TestCase):
    def setUp(self):
        self.primary = Monitor("main", (0, 0, 1920, 1040), True)
        self.left = Monitor("left", (-1280, 0, 0, 984))
        self.monitors = (self.primary, self.left)

    def test_anchor_respects_negative_coordinates_and_work_area(self):
        self.assertEqual(overlay_position(self.monitors, "left", "bottom_right", (300, 100), (0, 0)), (-316, 868))
        self.assertEqual(overlay_position(self.monitors, "main", "bottom_right", (300, 100), (0, 0)), (1604, 924))

    def test_missing_monitor_falls_back_and_returns_when_reconnected(self):
        self.assertEqual(choose_monitor((self.primary,), "left", (-1000, 0)), self.primary)
        self.assertEqual(overlay_position((self.primary,), "left", "top_left", (300, 100), (-1000, 0)), (16, 16))
        self.assertEqual(overlay_position(self.monitors, "left", "top_left", (300, 100), (16, 16)), (-1264, 16))

    def test_monitor_choice_is_independent_of_enumeration_order(self):
        self.assertEqual(choose_monitor(tuple(reversed(self.monitors)), "main", (-900, 200)), self.primary)
        self.assertEqual(choose_monitor(self.monitors, "", (-900, 200)), self.left)

    def test_free_position_and_oversized_overlay_are_recoverable(self):
        self.assertEqual(overlay_position(self.monitors, "", "free", (300, 100), (-900, 100)), (-900, 100))
        x, y = overlay_position(self.monitors, "left", "free", (300, 100), (9000, 9000))
        self.assertTrue(-1280 <= x <= -300 and 0 <= y <= 884)
        self.assertEqual(overlay_position(self.monitors, "left", "bottom_right", (2000, 2000), (0, 0)), (-1280, 0))
        self.assertEqual(overlay_position((), "left", "top_left", (300, 100), (42, 43)), (42, 43))

    def test_settings_modes_profiles_and_legacy_migration(self):
        settings = Settings.from_dict({"game_mode": "unity", "schema_version": 24})
        self.assertEqual((settings.rotation_overlay_monitor, settings.rotation_overlay_anchor), ("", "free"))
        settings.rotation_overlay_monitor = "left"
        settings.rotation_overlay_anchor = "bottom_right"
        settings.remember_display_preferences("unity")
        profile = Profile("Team", [], {}, "", "", overlay_by_game_mode={"unity": settings.overlay_preferences_snapshot()})
        restored = Settings.from_dict(settings.to_dict())
        restored.activate_display_preferences("retro")
        self.assertEqual(restored.rotation_overlay_monitor, "")
        restored.apply_profile_overlay(Profile.from_dict(profile.to_dict()).overlay_by_game_mode, "unity")
        self.assertEqual((restored.rotation_overlay_monitor, restored.rotation_overlay_anchor), ("left", "bottom_right"))

    def test_invalid_anchor_does_not_disable_free_placement(self):
        self.assertEqual(Settings(rotation_overlay_anchor="invalid").rotation_overlay_anchor, "free")

    def test_monitor_poll_only_rebuilds_after_layout_change(self):
        from dwm.ui_overlays import OverlayUI
        overlay = OverlayUI.__new__(OverlayUI)
        overlay.root = Mock()
        overlay.persistent_enabled = True
        overlay.persistent_window = Mock()
        overlay._monitor_signature = self.monitors
        overlay._render_persistent = Mock()
        with patch("dwm.ui_overlays.list_monitors", return_value=self.monitors):
            overlay._check_monitors()
        overlay._render_persistent.assert_not_called()
        with patch("dwm.ui_overlays.list_monitors", return_value=(self.primary,)):
            overlay._check_monitors()
        overlay._render_persistent.assert_called_once()
        overlay.root.after.assert_called_with(2000, overlay._check_monitors)
        overlay.persistent_enabled = False
        overlay.root.after.reset_mock()
        overlay._check_monitors()
        overlay.root.after.assert_not_called()

    @unittest.skipUnless(sys.platform == "win32", "Native Windows monitor enumeration")
    def test_native_windows_monitors_have_names_and_valid_work_areas(self):
        root = Mock()
        root.winfo_screenwidth.side_effect = AssertionError("native enumeration failed")
        monitors = list_monitors(root)
        self.assertTrue(monitors)
        self.assertTrue(any(monitor.primary for monitor in monitors))
        for monitor in monitors:
            self.assertTrue(monitor.identity)
            self.assertGreater(monitor.area[2], monitor.area[0])
            self.assertGreater(monitor.area[3], monitor.area[1])

    @unittest.skipUnless(sys.platform == "win32", "Native Windows overlay window")
    def test_real_overlay_reanchors_after_work_area_change_and_stops_timer(self):
        import tkinter as tk
        from dwm.ui_overlays import OverlayUI
        root = tk.Tk()
        root.withdraw()
        overlay = OverlayUI(root, focus_character=Mock(), save_overlay_position=Mock(), save_compact_geometry=Mock())
        try:
            with patch("dwm.ui_overlays.list_monitors", return_value=(Monitor("main", (0, 0, 640, 480), True),)):
                overlay.configure_persistent(enabled=True, x=0, y=0, opacity=88, locked=False,
                                             width=300, height=100, auto_width=False, monitor="main", anchor="bottom_right")
            root.update_idletasks()
            self.assertEqual((overlay.persistent_x, overlay.persistent_y), (324, 364))
            overlay._drag_start(Mock(x_root=20, y_root=20), None)
            self.assertIsNone(overlay._drag_pointer)
            overlay._drag_start(Mock(x_root=20, y_root=20), 123)
            self.assertEqual(overlay._drag_target_hwnd, 123)
            root.after_cancel(overlay._monitor_job)
            with patch("dwm.ui_overlays.list_monitors", return_value=(Monitor("main", (0, 0, 480, 320), True),)):
                overlay._check_monitors()
            self.assertEqual((overlay.persistent_x, overlay.persistent_y), (164, 204))
            overlay.close_all()
            self.assertIsNone(overlay._monitor_job)
            self.assertIsNone(overlay.persistent_window)
        finally:
            overlay.close_all()
            root.destroy()


if __name__ == "__main__":
    unittest.main()
