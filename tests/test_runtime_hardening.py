from __future__ import annotations

import os
import queue
import sys
import threading
import types
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from dwm.models import GameWindow

if os.name != "nt":
    hotkeys_stub = types.ModuleType("dwm.services.hotkeys_win")
    hotkeys_stub.HotkeyManager = object
    hotkeys_stub.parse_hotkey = lambda _text: (0, 0)
    sys.modules[hotkeys_stub.__name__] = hotkeys_stub

from dwm.app import WindowManagerApp  # noqa: E402
from dwm.services.focus import FocusError  # noqa: E402


class RuntimeHardeningTests(unittest.TestCase):
    def make_queue_app(self) -> WindowManagerApp:
        app = WindowManagerApp.__new__(WindowManagerApp)
        app._queue = queue.Queue()
        app._stop_event = threading.Event()
        app._game_mode_revision = 4
        app._structure_generation = 9
        app._refresh_again_requested = False
        app.root = Mock()
        app._sync_tray_state = Mock()
        app._finish_refresh = Mock()
        app._apply_windows = Mock()
        app._log = Mock()
        return app

    def test_queue_application_exception_does_not_block_following_message(self) -> None:
        app = self.make_queue_app()
        app._apply_windows.side_effect = RuntimeError("broken apply")
        app._queue.put(("windows", 4, 9, []))
        app._queue.put(("notice", 4, 9, "message suivant"))

        app._process_queue()

        app._finish_refresh.assert_called_once_with(
            success=False,
            error="broken apply",
        )
        self.assertIn(
            "message suivant",
            [call.args[0] for call in app._log.call_args_list],
        )
        self.assertEqual(app._queue.unfinished_tasks, 0)
        app.root.after.assert_called_once_with(100, app._process_queue)

    def test_stale_scan_is_finalized_and_requests_one_catchup(self) -> None:
        app = self.make_queue_app()
        app._queue.put(("windows", 4, 8, [GameWindow(101, "old", "old")]))

        app._process_queue()

        app._apply_windows.assert_not_called()
        self.assertTrue(app._refresh_again_requested)
        app._finish_refresh.assert_called_once_with(
            success=False,
            error="Résultat de scan périmé ignoré.",
        )

    def test_shutdown_rejects_queued_streamdeck_command_without_mutating(self) -> None:
        app = self.make_queue_app()
        app._stop_event.set()
        response = queue.Queue(maxsize=1)
        request_type = __import__("dwm.app", fromlist=["_QueuedStreamDeckRequest"])._QueuedStreamDeckRequest
        request = request_type(
            command="rotate",
            payload={"direction": "forward"},
            response_queue=response,
            request_id="req-1",
            deadline=10**9,
        )
        app._queue.put(("streamdeck", request))
        app._execute_streamdeck_command = Mock()

        app._process_queue()

        result = response.get_nowait()
        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], "app_closing")
        self.assertEqual(request.state, "expired")
        app._execute_streamdeck_command.assert_not_called()
        self.assertEqual(app._queue.unfinished_tasks, 0)

    def test_rotation_flush_drops_pending_mutation_after_shutdown(self) -> None:
        app = WindowManagerApp.__new__(WindowManagerApp)
        app._stop_event = threading.Event()
        app._stop_event.set()
        app._pending_rotation_delta = 3
        app._rotation_request_job = "job"
        app._rotate_by_delta = Mock()

        app._flush_rotation_requests()

        self.assertEqual(app._pending_rotation_delta, 0)
        self.assertIsNone(app._rotation_request_job)
        app._rotate_by_delta.assert_not_called()

    def test_reused_hwnd_is_rejected_immediately_before_focus(self) -> None:
        app = WindowManagerApp.__new__(WindowManagerApp)
        expected = GameWindow(
            101,
            "Nealla - Pandawa - Dofus",
            "Nealla",
            "Pandawa",
            pid=1001,
            window_class="UnityWndClass",
            game_mode="unity",
            process_image="C:/Dofus/Dofus.exe",
        )
        current = GameWindow(
            101,
            "Nat - Eniripsa - Dofus",
            "Nat",
            "Eniripsa",
            pid=2002,
            window_class="UnityWndClass",
            game_mode="unity",
            process_image="C:/Dofus/Dofus.exe",
        )
        app._all_windows = {101: expected}
        app._managed_order = [101]
        app._streamdeck_order = [101]
        app._ignored = set()
        app._active_game_hwnd = 101
        app.rotation_index = 0
        app.attention_state = SimpleNamespace(clear=Mock())
        app.settings = SimpleNamespace(
            retro_title_keyword="dofus retro v",
            retro_process_keyword="",
        )
        app._refresh_after_identity_mismatch = Mock()
        app.runtime_metrics = None

        with (
            patch("dwm.app.revalidate_game_window", return_value=current),
            patch("dwm.app.focus_hwnd") as focus,
        ):
            with self.assertRaises(FocusError):
                app._focus_hwnd_measured(101)

        app._refresh_after_identity_mismatch.assert_called_once_with(101)
        focus.assert_not_called()


if __name__ == "__main__":
    unittest.main()
