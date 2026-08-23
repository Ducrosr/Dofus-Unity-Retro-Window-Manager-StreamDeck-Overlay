from __future__ import annotations

import os
import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from dwm.models import GameWindow
from dwm.services.display_overlay import CharacterDisplay
from dwm.ui_overlays import (
    DISPLAY_MAX_WIDTH,
    DISPLAY_MIN_WIDTH,
    OverlayUI,
    SWAP_NOTIFICATION_DEBOUNCE_MS,
    _adaptive_display_width,
)

if os.name != "nt":
    hotkeys_stub = types.ModuleType("dwm.services.hotkeys_win")
    hotkeys_stub.HotkeyManager = object
    hotkeys_stub.parse_hotkey = lambda _text: (0, 0)
    sys.modules[hotkeys_stub.__name__] = hotkeys_stub

from dwm.app import ROTATION_COALESCE_MS, WindowManagerApp  # noqa: E402


class FakeRoot:
    def __init__(self) -> None:
        self.callbacks: dict[str, object] = {}
        self.delays: dict[str, int] = {}
        self.cancelled: list[str] = []
        self._next_job = 0

    def after(self, delay: int, callback):
        self._next_job += 1
        job = f"job-{self._next_job}"
        self.callbacks[job] = callback
        self.delays[job] = delay
        return job

    def after_cancel(self, job: str) -> None:
        self.cancelled.append(job)
        self.callbacks.pop(job, None)

    def run(self, job: str) -> None:
        callback = self.callbacks.pop(job)
        callback()


def display(hwnd: int, *, active: bool) -> CharacterDisplay:
    return CharacterDisplay(
        hwnd=hwnd,
        pseudo=f"Character {hwnd}",
        character_class="Cra",
        alias="",
        position=hwnd,
        total=2,
        active=active,
    )


class FocusResponsivenessTests(unittest.TestCase):
    def test_plain_focus_uses_the_in_place_refresh(self) -> None:
        app = WindowManagerApp.__new__(WindowManagerApp)
        app._active_game_hwnd = 101
        app._managed_order = [101, 102]
        app.rotation_index = 0
        app.attention_state = SimpleNamespace(clear=Mock(return_value=False))
        app.settings = SimpleNamespace(swap_notification_enabled=False)
        app._refresh_focus_views = Mock()
        app.update_listboxes = Mock()

        app._record_character_focus(102, notify=False)

        self.assertEqual(app.rotation_index, 1)
        app._refresh_focus_views.assert_called_once_with()
        app.update_listboxes.assert_not_called()

    def test_attention_clear_still_rebuilds_changed_queue_content(self) -> None:
        app = WindowManagerApp.__new__(WindowManagerApp)
        app._active_game_hwnd = 101
        app._managed_order = [101, 102]
        app.rotation_index = 0
        app.attention_state = SimpleNamespace(clear=Mock(return_value=True))
        app.settings = SimpleNamespace(swap_notification_enabled=False)
        app._refresh_focus_views = Mock()
        app.update_listboxes = Mock()

        app._record_character_focus(102, notify=False)

        app.update_listboxes.assert_called_once_with()
        app._refresh_focus_views.assert_not_called()

    def test_popup_uses_its_independent_portrait_and_icon_preferences(self) -> None:
        app = WindowManagerApp.__new__(WindowManagerApp)
        app._active_game_hwnd = 101
        app._managed_order = [101]
        app._all_windows = {
            101: GameWindow(101, "Window 101", "Character 101", "Cra")
        }
        app.rotation_index = 0
        app.aliases = {}
        app.attention_state = SimpleNamespace(clear=Mock(return_value=False))
        app.settings = SimpleNamespace(
            swap_notification_enabled=True,
            swap_notification_anchor="top_center",
            swap_notification_duration_ms=900,
            swap_notification_opacity=88,
            swap_notification_layout=None,
            show_popup_portraits=False,
            show_popup_badges=True,
            character_visuals={"Character 101": {"badge": "ankama_force"}},
        )
        app.overlay_ui = Mock()

        app._record_character_focus(101, notify=True)

        kwargs = app.overlay_ui.show_swap_notification.call_args.kwargs
        self.assertFalse(kwargs["show_portrait"])
        self.assertTrue(kwargs["show_badge"])

    def test_rapid_rotation_requests_focus_only_the_net_destination(self) -> None:
        app = WindowManagerApp.__new__(WindowManagerApp)
        app.root = FakeRoot()
        app._managed_order = [101, 102, 103]
        app._pending_rotation_delta = 0
        app._rotation_request_job = None
        app._rotate_by_delta = Mock(return_value=True)

        app.request_rotation("forward")
        first_job = app._rotation_request_job
        app.request_rotation("forward")
        app.request_rotation("forward")
        app.request_rotation("backward")

        self.assertEqual(len(app.root.callbacks), 1)
        self.assertEqual(app.root.delays[first_job], ROTATION_COALESCE_MS)
        app.root.run(first_job)
        app._rotate_by_delta.assert_called_once_with(2)
        self.assertEqual(app._pending_rotation_delta, 0)
        self.assertIsNone(app._rotation_request_job)

    def test_coalesced_rotation_skips_intermediate_focus_calls(self) -> None:
        app = WindowManagerApp.__new__(WindowManagerApp)
        app._all_windows = {
            hwnd: GameWindow(hwnd, f"Window {hwnd}", f"Character {hwnd}", "Cra")
            for hwnd in (101, 102, 103)
        }
        app._managed_order = [101, 102, 103]
        app._ignored = set()
        app.rotation_index = 0
        app._privilege_mismatch_suspected = False
        app._record_character_focus = Mock()
        app._log = Mock()
        app.update_listboxes = Mock()
        app.refresh_windows = Mock()

        with (
            patch("dwm.app.is_window", return_value=True),
            patch("dwm.app.focus_hwnd") as focus,
        ):
            self.assertTrue(app._rotate_by_delta(5))

        focus.assert_called_once_with(103)
        app._record_character_focus.assert_called_once_with(103, notify=True)
        app.update_listboxes.assert_not_called()

    def test_streamdeck_rotation_joins_the_same_coalesced_queue(self) -> None:
        app = WindowManagerApp.__new__(WindowManagerApp)
        app.request_rotation = Mock(return_value=True)

        result = app._execute_streamdeck_command("rotate", {"direction": "forward"})

        app.request_rotation.assert_called_once_with("forward")
        self.assertEqual(
            result,
            {"ok": True, "accepted": True, "direction": "forward"},
        )


class OverlayResponsivenessTests(unittest.TestCase):
    def test_adaptive_width_uses_natural_content_size_with_safe_bounds(self) -> None:
        self.assertEqual(_adaptive_display_width(104), 104)
        self.assertEqual(_adaptive_display_width(20), DISPLAY_MIN_WIDTH)
        self.assertEqual(_adaptive_display_width(1200), DISPLAY_MAX_WIDTH)
        self.assertEqual(_adaptive_display_width(700, 460), 460)

    def test_focus_only_update_does_not_rebuild_overlay_rows(self) -> None:
        overlay = OverlayUI.__new__(OverlayUI)
        overlay.entries = [display(1, active=True), display(2, active=False)]
        overlay.attention_count = 0
        overlay.persistent_enabled = True
        overlay._persistent_rows = {1: Mock(), 2: Mock()}
        overlay._ensure_persistent = Mock()
        overlay._refresh_persistent_focus = Mock()
        overlay._render_persistent = Mock()
        overlay._refresh_compact_focus = Mock()
        overlay._refresh_compact = Mock()

        overlay.update_characters(
            [display(1, active=False), display(2, active=True)],
            attention_count=0,
        )

        overlay._refresh_persistent_focus.assert_called_once_with()
        overlay._render_persistent.assert_not_called()
        overlay._refresh_compact_focus.assert_called_once_with()
        overlay._refresh_compact.assert_not_called()

    def test_rapid_notifications_keep_only_the_latest_request(self) -> None:
        overlay = OverlayUI.__new__(OverlayUI)
        overlay.root = FakeRoot()
        overlay.toast_show_job = None
        overlay._toast_request = None
        overlay._show_swap_notification_now = Mock()

        overlay.show_swap_notification(display(1, active=True), anchor="top_left", duration_ms=900)
        first_job = overlay.toast_show_job
        overlay.show_swap_notification(display(2, active=True), anchor="top_right", duration_ms=1200)
        latest_job = overlay.toast_show_job

        self.assertIn(first_job, overlay.root.cancelled)
        self.assertEqual(overlay.root.delays[latest_job], SWAP_NOTIFICATION_DEBOUNCE_MS)
        overlay.root.run(latest_job)
        request = overlay._show_swap_notification_now.call_args.args[0]
        self.assertEqual(request.entry.hwnd, 2)
        self.assertEqual(request.anchor, "top_right")
        self.assertEqual(request.duration_ms, 1200)

    def test_manual_resize_disables_automatic_width(self) -> None:
        overlay = OverlayUI.__new__(OverlayUI)
        overlay.persistent_window = Mock()
        overlay._resize_pointer = (10, 20)
        overlay._resize_window_size = (110, 90)
        overlay.persistent_auto_width = True
        overlay.persistent_x = 24
        overlay.persistent_y = 160
        overlay._apply_persistent_text_scale = Mock()
        overlay.save_overlay_size = Mock()
        overlay._render_persistent = Mock()

        overlay._resize_motion(SimpleNamespace(x_root=50, y_root=60))
        overlay._resize_release(None)

        self.assertFalse(overlay.persistent_auto_width)
        self.assertEqual((overlay.persistent_width, overlay.persistent_height), (150, 130))
        overlay.save_overlay_size.assert_called_once_with(150, 130, auto_width=False)


if __name__ == "__main__":
    unittest.main()
