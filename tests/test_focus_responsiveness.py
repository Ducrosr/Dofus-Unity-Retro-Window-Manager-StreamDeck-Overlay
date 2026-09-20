from __future__ import annotations

import os
import sys
import threading
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
    _overlay_control_visibility,
)

if os.name != "nt":
    hotkeys_stub = types.ModuleType("dwm.services.hotkeys_win")
    hotkeys_stub.HotkeyManager = object
    hotkeys_stub.parse_hotkey = lambda _text: (0, 0)
    sys.modules[hotkeys_stub.__name__] = hotkeys_stub

from dwm.app import ROTATION_COALESCE_MS, WindowManagerApp  # noqa: E402
from dwm.services.focus import FocusError  # noqa: E402


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

    def test_reused_hwnd_is_invalidated_before_focus(self) -> None:
        app = WindowManagerApp.__new__(WindowManagerApp)
        app._stop_event = threading.Event()
        app._all_windows = {
            101: GameWindow(
                101,
                "Korra - Féca - Dofus",
                "Korra",
                "Féca",
                pid=100,
                window_class="UnityWndClass",
                game_mode="unity",
            )
        }
        app.settings = SimpleNamespace(
            retro_title_keyword="dofus retro v",
            retro_process_keyword="",
        )
        app._invalidate_window_target = Mock()
        app.refresh_windows = Mock()

        with (
            patch("dwm.app.revalidate_game_window", return_value=None),
            patch("dwm.app.focus_hwnd") as focus,
        ):
            with self.assertRaises(FocusError):
                app._focus_hwnd_measured(101)

        focus.assert_not_called()
        app._invalidate_window_target.assert_called_once_with(101)
        app.refresh_windows.assert_called_once_with(quiet=True, force=True)

    def test_popup_focus_failure_preserves_rotation_index(self) -> None:
        app = WindowManagerApp.__new__(WindowManagerApp)
        app._stop_event = threading.Event()
        app._popup_watch_enabled = True
        app.popup_watcher = Mock()
        app.popup_watcher.is_current_event.return_value = True
        app._managed_order = [101, 102]
        app._ignored = set()
        app.rotation_index = 0
        app._popup_global_cooldown_until = 0.0
        app._popup_global_cooldown_sec = 2.0
        app._focus_hwnd_measured = Mock(side_effect=FocusError("blocked"))
        app._record_character_focus = Mock()
        app._log = Mock()
        event = SimpleNamespace(
            hwnd=102,
            title="Nat - Dofus Retro v1.44",
            generation=3,
        )

        app._handle_popup_event(event)

        self.assertEqual(app.rotation_index, 0)
        app._record_character_focus.assert_not_called()

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
    def test_hidden_overlay_controls_keep_drag_and_drop_available(self) -> None:
        self.assertEqual(
            _overlay_control_visibility(
                locked=False,
                show_title=False,
                show_reorder_buttons=False,
            ),
            (False, False, True),
        )
        self.assertEqual(
            _overlay_control_visibility(
                locked=True,
                show_title=True,
                show_reorder_buttons=True,
            ),
            (False, False, False),
        )

    def test_adaptive_width_uses_natural_content_size_with_safe_bounds(self) -> None:
        self.assertEqual(_adaptive_display_width(104), 104)
        self.assertEqual(_adaptive_display_width(20), DISPLAY_MIN_WIDTH)
        self.assertEqual(_adaptive_display_width(1200), 1200)
        self.assertEqual(_adaptive_display_width(2400), DISPLAY_MAX_WIDTH)
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

    def test_horizontal_drag_order_uses_left_to_right_midpoints(self) -> None:
        overlay = OverlayUI.__new__(OverlayUI)
        overlay.entries = [
            display(1, active=False),
            display(2, active=False),
            display(3, active=True),
        ]
        overlay.persistent_orientation = "horizontal"
        overlay._drag_target_hwnd = 3
        overlay._drop_target_index = None
        overlay._drop_preview_hwnd = None
        overlay.palette = {"attention": "#ff9900"}
        overlay._persistent_rows = {
            hwnd: SimpleNamespace(
                winfo_rootx=lambda start=start: start,
                winfo_width=lambda: 80,
                winfo_rooty=lambda: 0,
                winfo_height=lambda: 40,
                configure=Mock(),
            )
            for hwnd, start in ((1, 0), (2, 100), (3, 200))
        }

        overlay._update_drop_preview(20, 999)

        self.assertEqual(overlay._drop_target_index, 0)
        self.assertEqual(overlay._drop_preview_hwnd, 1)

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

    def test_palette_change_keeps_same_persistent_toplevel(self) -> None:
        overlay = OverlayUI.__new__(OverlayUI)
        overlay._closed = False
        overlay.palette = {}
        window = Mock()
        overlay.persistent_window = window
        overlay.persistent_enabled = True
        overlay.compact_window = None
        overlay._destroy_persistent = Mock()
        overlay._render_persistent = Mock()
        overlay._refresh_compact = Mock()

        overlay.set_palette({"bg": "#111111"})

        self.assertIs(overlay.persistent_window, window)
        overlay._destroy_persistent.assert_not_called()
        overlay._render_persistent.assert_called_once_with()

    def test_lock_change_restyles_same_persistent_toplevel(self) -> None:
        overlay = OverlayUI.__new__(OverlayUI)
        overlay._closed = False
        overlay.root = Mock()
        overlay.palette = {"line": "#123456"}
        window = Mock()
        overlay.persistent_window = window
        overlay.obs_capture = True
        overlay._monitor_job = "monitor-job"
        overlay._ensure_persistent = Mock()
        overlay._render_persistent = Mock()

        with patch("dwm.ui_overlays._apply_non_activating_style") as apply_style:
            overlay.configure_persistent(
                enabled=True,
                x=10,
                y=20,
                opacity=88,
                locked=True,
                width=300,
                auto_width=True,
                height=0,
            )

        self.assertIs(overlay.persistent_window, window)
        apply_style.assert_called_once_with(window, click_through=True)
        overlay._render_persistent.assert_called_once_with()

    def test_close_all_is_terminal_and_idempotent(self) -> None:
        overlay = OverlayUI.__new__(OverlayUI)
        overlay._closed = False
        overlay.hide_swap_notification = Mock()
        overlay._destroy_persistent = Mock()
        overlay.close_compact = Mock()

        overlay.close_all()
        overlay.close_all()

        self.assertTrue(overlay._closed)
        overlay.hide_swap_notification.assert_called_once_with()
        overlay._destroy_persistent.assert_called_once_with()
        overlay.close_compact.assert_called_once_with(show_root=False)

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
