from __future__ import annotations

import os
import queue
import sys
import threading
import types
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

if os.name != "nt":
    hotkeys_stub = types.ModuleType("dwm.services.hotkeys_win")
    hotkeys_stub.HotkeyManager = object
    hotkeys_stub.parse_hotkey = lambda _text: (0, 0)
    sys.modules.setdefault(hotkeys_stub.__name__, hotkeys_stub)

from dwm.app import WindowManagerApp  # noqa: E402


class _Root:
    def __init__(self) -> None:
        self.after_calls: list[tuple[int, object]] = []

    def after(self, delay: int, callback):
        self.after_calls.append((delay, callback))
        return f"job-{len(self.after_calls)}"


class RuntimeReliabilityTests(unittest.TestCase):
    def make_app(self) -> WindowManagerApp:
        app = WindowManagerApp.__new__(WindowManagerApp)
        app._queue = queue.Queue()
        app._queue_batch_limit = 64
        app._stop_event = threading.Event()
        app.root = _Root()
        app._game_mode_revision = 3
        app._structure_generation = 7
        app._win_event_generation = 5
        app.game_mode = "unity"
        app._apply_windows = Mock()
        app._finish_refresh = Mock()
        app._sync_tray_state = Mock()
        app._log = Mock()
        app._execute_streamdeck_command = Mock(return_value={"ok": True})
        return app

    def test_queue_exception_does_not_block_following_message_or_acknowledgement(self) -> None:
        app = self.make_app()
        app._apply_windows.side_effect = [RuntimeError("boom"), None]
        app._queue.put(("windows", 3, 7, ["bad"]))
        app._queue.put(("windows", 3, 7, ["good"]))

        app._process_queue()

        self.assertEqual(app._apply_windows.call_count, 2)
        self.assertEqual(
            [
                (call.kwargs["applied"], call.kwargs["catch_up"])
                for call in app._finish_refresh.call_args_list
            ],
            [(False, True), (True, False)],
        )
        self.assertEqual(app._queue.unfinished_tasks, 0)
        self.assertTrue(app.root.after_calls)

    def test_stale_scan_is_finalized_but_never_applied(self) -> None:
        app = self.make_app()
        app._queue.put(("windows", 3, 6, ["stale"]))

        app._process_queue()

        app._apply_windows.assert_not_called()
        app._finish_refresh.assert_called_once_with(applied=False, catch_up=True)

    def test_shutdown_rejects_pending_mutation_without_executing_it(self) -> None:
        app = self.make_app()
        app._stop_event.set()
        response = queue.Queue(maxsize=1)
        request_state = {
            "request_id": "r1",
            "state": "queued",
            "deadline": 9999999999.0,
            "lock": threading.Lock(),
        }
        app._queue.put(("streamdeck", "rotate", {"direction": "forward"}, response, request_state))

        app._process_queue()

        app._execute_streamdeck_command.assert_not_called()
        result = response.get_nowait()
        self.assertEqual(result["error_code"], "app_closing")
        self.assertEqual(app._queue.unfinished_tasks, 0)

    def test_shutdown_flush_discards_pending_rotation(self) -> None:
        app = self.make_app()
        app._pending_rotation_delta = 3
        app._rotation_request_job = "job"
        app._rotate_by_delta = Mock()
        app._stop_event.set()

        app._flush_rotation_requests()

        self.assertEqual(app._pending_rotation_delta, 0)
        self.assertIsNone(app._rotation_request_job)
        app._rotate_by_delta.assert_not_called()

    def test_stale_hook_event_is_ignored(self) -> None:
        app = self.make_app()
        app._apply_win_event = Mock()
        app._queue.put(("wevt", 4, "unity", "create", 101))

        app._process_queue()

        app._apply_win_event.assert_not_called()

    def test_cancelled_streamdeck_request_never_starts(self) -> None:
        app = self.make_app()
        response = queue.Queue(maxsize=1)
        request_state = {
            "request_id": "r2",
            "state": "cancelled",
            "deadline": 9999999999.0,
            "lock": threading.Lock(),
        }

        app._process_streamdeck_queue_item(
            ("streamdeck", "rotate", {"direction": "forward"}, response, request_state)
        )

        app._execute_streamdeck_command.assert_not_called()
        self.assertTrue(response.empty())


if __name__ == "__main__":
    unittest.main()
