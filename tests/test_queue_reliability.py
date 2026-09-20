from __future__ import annotations

import queue
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from dwm.app import (
    QUEUE_BATCH_LIMIT,
    WindowManagerApp,
    _QueuedStreamDeckCommand,
)
from dwm.models import GameWindow
from dwm.services.focus import FocusError


class _FakeRoot:
    def __init__(self) -> None:
        self.after_calls: list[tuple[int, object]] = []
        self.cancelled: list[object] = []

    def after(self, delay: int, callback):
        self.after_calls.append((delay, callback))
        return f"job-{len(self.after_calls)}"

    def after_cancel(self, job) -> None:
        self.cancelled.append(job)


def _pump_app() -> WindowManagerApp:
    app = WindowManagerApp.__new__(WindowManagerApp)
    app.root = _FakeRoot()
    app._queue = queue.Queue()
    app._stop_event = threading.Event()
    app._game_mode_revision = 3
    app._structure_generation = 7
    app._event_hook_generation = 11
    app._refresh_again_requested = False
    app._apply_windows = Mock()
    app._finish_refresh = Mock()
    app._apply_win_event = Mock()
    app._sync_tray_state = Mock()
    app._log = Mock()
    return app


class QueueReliabilityTests(unittest.TestCase):
    def test_apply_exception_does_not_poison_following_queue_message(self) -> None:
        app = _pump_app()
        app._apply_windows.side_effect = [RuntimeError("boom"), None]
        app._queue.put(("windows", 3, 7, [GameWindow(1, "A - Dofus", "A")]))
        app._queue.put(("windows", 3, 7, [GameWindow(2, "B - Dofus", "B")]))

        app._process_queue()

        self.assertEqual(app._apply_windows.call_count, 2)
        self.assertEqual(app._finish_refresh.call_count, 2)
        self.assertEqual(app._queue.unfinished_tasks, 0)
        self.assertTrue(app.root.after_calls)

    def test_queue_batch_is_bounded_and_rearms_immediately(self) -> None:
        app = _pump_app()
        app._handle_tray_action = Mock()
        for _ in range(QUEUE_BATCH_LIMIT + 5):
            app._queue.put(("tray", "show"))

        app._process_queue()

        self.assertEqual(app._handle_tray_action.call_count, QUEUE_BATCH_LIMIT)
        self.assertEqual(app.root.after_calls[-1][0], 0)
        self.assertEqual(app._queue.qsize(), 5)

    def test_stale_scan_result_is_finalized_and_requests_one_catchup(self) -> None:
        app = _pump_app()
        app._queue.put(("windows", 3, 6, [GameWindow(1, "A - Dofus", "A")]))

        app._process_queue()

        app._apply_windows.assert_not_called()
        app._finish_refresh.assert_called_once()
        self.assertTrue(app._refresh_again_requested)

    def test_old_hook_generation_cannot_mutate_current_state(self) -> None:
        app = _pump_app()
        app._queue.put(("wevt", 3, 10, "destroy", 123))

        app._process_queue()

        app._apply_win_event.assert_not_called()

    def test_streamdeck_mutation_rejects_stale_mode_before_side_effect(self) -> None:
        app = _pump_app()
        app.game_mode = "unity"
        app._active_profile_name = "Team"
        app.request_rotation = Mock(return_value=True)

        result = app._execute_streamdeck_command(
            "rotate",
            {
                "direction": "forward",
                "game_mode": "retro",
                "profile": "Team",
            },
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "context_changed")
        app.request_rotation.assert_not_called()

    def test_shutdown_cancels_queued_streamdeck_mutation(self) -> None:
        app = _pump_app()
        app._execute_streamdeck_command = Mock()
        request = _QueuedStreamDeckCommand(
            "rotate",
            {"direction": "forward"},
            request_id="req-1",
            deadline=time.monotonic() + 10,
        )
        app._queue.put(("streamdeck", request))
        app._stop_event.set()

        app._process_queue()
        result = request.response.get_nowait()

        self.assertEqual(result["error_code"], "closing")
        self.assertEqual(request.state, "cancelled")
        app._execute_streamdeck_command.assert_not_called()

    def test_expired_queued_command_is_never_executed_later(self) -> None:
        app = _pump_app()
        app._execute_streamdeck_command = Mock()
        result = app._dispatch_streamdeck_command(
            "rotate",
            {
                "direction": "forward",
                "_bridge": {
                    "request_id": "req-expire",
                    "deadline_monotonic": time.monotonic() - 1.0,
                },
            },
        )
        self.assertEqual(result["error_code"], "command_expired")

        item = app._queue.get_nowait()
        try:
            app._process_queue_item(item)
        finally:
            app._queue.task_done()
        app._execute_streamdeck_command.assert_not_called()


class TargetIdentityTests(unittest.TestCase):
    def test_reused_hwnd_is_invalidated_before_focus(self) -> None:
        app = WindowManagerApp.__new__(WindowManagerApp)
        expected = GameWindow(
            42,
            "Nealla - Féca - 3.4",
            "Nealla",
            "Féca",
            process_id=100,
            window_class="UnityWndClass",
            game_mode="unity",
            process_image=r"C:\Games\Dofus.exe",
        )
        current = GameWindow(
            42,
            "Syra - Féca - 3.4",
            "Syra",
            "Féca",
            process_id=200,
            window_class="UnityWndClass",
            game_mode="unity",
            process_image=r"C:\Games\Dofus.exe",
        )
        app._all_windows = {42: expected}
        app._managed_order = [42]
        app._streamdeck_order = [42]
        app._ignored = set()
        app._active_game_hwnd = 42
        app.rotation_index = 0
        app._structure_generation = 1
        app._windows_sig = ((42, expected.title),)
        app.attention_state = Mock()
        app._reconcile_character_roster = Mock()
        app.update_listboxes = Mock()
        app._update_popup_watcher_targets = Mock()
        app.refresh_windows = Mock()
        app._log = Mock()
        app.game_mode = "unity"
        app.settings = SimpleNamespace(
            retro_title_keyword="dofus retro v",
            retro_process_keyword="",
        )

        with (
            patch("dwm.app.is_window", return_value=True),
            patch("dwm.app.inspect_game_window", return_value=current),
        ):
            self.assertIsNone(app._revalidate_focus_target(42))

        self.assertNotIn(42, app._all_windows)
        self.assertNotIn(42, app._managed_order)
        self.assertNotIn(42, app._streamdeck_order)
        self.assertIsNone(app._active_game_hwnd)
        app.refresh_windows.assert_called_once_with(quiet=True, force=True)

    def test_popup_focus_failure_does_not_move_rotation_cursor(self) -> None:
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
        app._focus_hwnd_measured = Mock(side_effect=FocusError("refus"))
        app._record_character_focus = Mock()
        app._log = Mock()
        event = SimpleNamespace(hwnd=102, title="B", generation=4)

        app._handle_popup_event(event)

        self.assertEqual(app.rotation_index, 0)
        app._record_character_focus.assert_not_called()


if __name__ == "__main__":
    unittest.main()
