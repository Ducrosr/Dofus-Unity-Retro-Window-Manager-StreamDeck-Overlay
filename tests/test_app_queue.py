from __future__ import annotations

import os
import queue
import sys
import threading
import time
import types
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

if os.name != "nt":
    hotkeys_stub = types.ModuleType("dwm.services.hotkeys_win")
    hotkeys_stub.HotkeyManager = object
    hotkeys_stub.parse_hotkey = lambda _text: (0, 0)
    sys.modules[hotkeys_stub.__name__] = hotkeys_stub

from dwm.app import WindowManagerApp, _StreamDeckRequest  # noqa: E402


class _FakeRoot:
    def __init__(self) -> None:
        self.after_calls: list[tuple[int, object]] = []

    def after(self, delay: int, callback):
        self.after_calls.append((delay, callback))
        return f"job-{len(self.after_calls)}"


class AppQueueTests(unittest.TestCase):
    def make_app(self) -> WindowManagerApp:
        app = WindowManagerApp.__new__(WindowManagerApp)
        app._queue = queue.Queue()
        app._stop_event = threading.Event()
        app._game_mode_revision = 4
        app._structure_generation = 7
        app._event_hook_generation = 3
        app._refresh_again_requested = False
        app.root = _FakeRoot()
        app.logger = Mock()
        app._log = Mock()
        app._sync_tray_state = Mock()
        app._apply_windows = Mock()
        app._finish_refresh = Mock()
        app._execute_streamdeck_command = Mock(return_value={"ok": True})
        return app

    def test_exception_in_scan_application_does_not_kill_queue_pump(self) -> None:
        app = self.make_app()
        app._apply_windows.side_effect = RuntimeError("boom")
        app._queue.put(("windows", 4, 7, []))
        app._queue.put(("notice", 4, 7, "message suivant"))

        app._process_queue()

        app._finish_refresh.assert_called_once_with()
        self.assertTrue(
            any(
                call.args and call.args[0] == "message suivant"
                for call in app._log.call_args_list
            )
        )
        self.assertEqual(app._queue.unfinished_tasks, 0)
        self.assertTrue(app.root.after_calls)

    def test_scan_result_started_before_structure_change_is_rejected_with_barrier(self) -> None:
        entered = threading.Event()
        release = threading.Event()
        queued = threading.Event()

        class SignalingQueue(queue.Queue):
            def put(self, item, block=True, timeout=None):
                super().put(item, block=block, timeout=timeout)
                if item[0] == "windows":
                    queued.set()

        app = self.make_app()
        app._queue = SignalingQueue()
        app._refresh_inflight = False
        app._last_scan_monotonic = 0.0
        app._min_scan_interval_sec = 0.0
        app._scan_started_monotonic = None
        app.game_mode = "unity"
        app.game_label = "Unity"
        app.settings = SimpleNamespace(
            retro_title_keyword="dofus retro v",
            retro_process_keyword="",
        )
        app._apply_windows = Mock()
        app._finish_refresh = Mock()

        def blocked_scan(*_args):
            entered.set()
            if not release.wait(2):
                raise AssertionError("scan barrier was not released")
            return [object()]

        with (
            patch("dwm.app.list_game_windows", side_effect=blocked_scan),
            patch("dwm.app.get_last_enum_error", return_value=""),
        ):
            self.assertTrue(app.refresh_windows(force=True))
            self.assertTrue(entered.wait(1))
            app._structure_generation += 1
            release.set()
            self.assertTrue(queued.wait(1))
            app._process_queue()

        app._apply_windows.assert_not_called()
        app._finish_refresh.assert_called_once_with()
        self.assertTrue(app._refresh_again_requested)

    def test_stale_scan_is_finalized_and_requests_one_catchup(self) -> None:
        app = self.make_app()
        app._queue.put(("windows", 4, 6, ["ancien"]))

        app._process_queue()

        app._apply_windows.assert_not_called()
        app._finish_refresh.assert_called_once_with()
        self.assertTrue(app._refresh_again_requested)
        self.assertEqual(app._queue.unfinished_tasks, 0)

    def test_schedule_refresh_rearms_even_if_refresh_raises(self) -> None:
        app = self.make_app()
        app.settings = SimpleNamespace(
            refresh_seconds=5,
            adaptive_performance_enabled=True,
        )
        app.auto_refresh_enabled = SimpleNamespace(get=lambda: True)
        app.win_events = None
        app._all_windows = {}
        app.refresh_windows = Mock(side_effect=RuntimeError("scan failed"))

        app._schedule_refresh()

        self.assertEqual(len(app.root.after_calls), 1)
        delay, callback = app.root.after_calls[0]
        self.assertGreaterEqual(delay, 1000)
        self.assertEqual(callback, app._schedule_refresh)

    def test_busy_queue_yields_back_to_tk_instead_of_draining_forever(self) -> None:
        app = self.make_app()
        for index in range(100):
            app._queue.put(("notice", 4, 7, f"notice-{index}"))

        app._process_queue()

        self.assertGreater(app._queue.qsize(), 0)
        self.assertTrue(app.root.after_calls)
        self.assertEqual(app.root.after_calls[-1][0], 1)

    def test_expired_streamdeck_request_is_cancelled_before_mutation(self) -> None:
        app = self.make_app()
        response: "queue.Queue[dict[str, object]]" = queue.Queue(maxsize=1)
        request = _StreamDeckRequest(
            request_id="request-1",
            command="rotate",
            payload={"direction": "forward"},
            deadline=time.monotonic() - 1.0,
            response_queue=response,
        )
        app._queue.put(("streamdeck", request))

        app._process_queue()

        app._execute_streamdeck_command.assert_not_called()
        result = response.get_nowait()
        self.assertEqual(result["error_code"], "deadline_exceeded")
        self.assertEqual(result["request_id"], "request-1")

    def test_started_streamdeck_request_cannot_be_cancelled_as_not_started(self) -> None:
        request = _StreamDeckRequest(
            request_id="request-2",
            command="focus",
            payload={},
            deadline=time.monotonic() + 10,
            response_queue=queue.Queue(maxsize=1),
        )

        self.assertTrue(request.try_start(time.monotonic()))
        self.assertFalse(request.cancel_if_not_started())


if __name__ == "__main__":
    unittest.main()
