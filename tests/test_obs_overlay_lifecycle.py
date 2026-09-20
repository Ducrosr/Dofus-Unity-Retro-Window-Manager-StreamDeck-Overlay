from __future__ import annotations

import unittest
from unittest.mock import Mock

from dwm.ui_overlays import DEFAULT_PALETTE, OverlayUI


class OBSOverlayLifecycleTests(unittest.TestCase):
    def test_palette_update_rerenders_without_recreating_persistent_window(self) -> None:
        overlay = OverlayUI.__new__(OverlayUI)
        overlay._closed = False
        overlay.palette = dict(DEFAULT_PALETTE)
        overlay.persistent_window = Mock()
        overlay.persistent_enabled = True
        overlay.compact_window = None
        overlay._render_persistent = Mock()
        overlay._destroy_persistent = Mock()
        overlay._refresh_compact = Mock()

        original_window = overlay.persistent_window
        overlay.set_palette({"accent": "#123456"})

        self.assertIs(overlay.persistent_window, original_window)
        overlay._destroy_persistent.assert_not_called()
        overlay._render_persistent.assert_called_once_with()

    def test_lock_change_keeps_same_persistent_window(self) -> None:
        overlay = OverlayUI.__new__(OverlayUI)
        overlay._closed = False
        overlay.persistent_window = Mock()
        overlay.persistent_locked = False
        overlay._ensure_persistent = Mock()
        overlay._render_persistent = Mock()
        overlay._destroy_persistent = Mock()
        overlay._monitor_job = "existing-monitor-job"

        original_window = overlay.persistent_window
        overlay.configure_persistent(
            enabled=True,
            x=24,
            y=160,
            opacity=88,
            locked=True,
            width=300,
            auto_width=True,
            height=0,
        )

        self.assertIs(overlay.persistent_window, original_window)
        overlay._destroy_persistent.assert_not_called()
        overlay._ensure_persistent.assert_called_once_with()
        overlay._render_persistent.assert_called_once_with()

    def test_obs_idle_popup_is_kept_alive_until_terminal_close(self) -> None:
        overlay = OverlayUI.__new__(OverlayUI)
        overlay.root = Mock()
        overlay._closed = False
        overlay._obs_capture_enabled = True
        overlay._obs_popup_idle = Mock()
        overlay._obs_popup_style = Mock()
        overlay.toast_job = None
        overlay.toast_show_job = None
        overlay._toast_request = None
        overlay._toast_images = []
        window = Mock()
        overlay.toast_window = window
        overlay._destroy_persistent = Mock()
        overlay.close_compact = Mock()

        overlay._hide_visible_toast()

        self.assertIs(overlay.toast_window, window)
        window.destroy.assert_not_called()
        overlay._obs_popup_idle.assert_called_once_with(window)
        overlay._obs_popup_style.assert_called_once_with(window)

        overlay.close_all()
        overlay.close_all()

        window.destroy.assert_called_once_with()
        overlay._destroy_persistent.assert_called_once_with()
        overlay.close_compact.assert_called_once_with(show_root=False)


if __name__ == "__main__":
    unittest.main()
