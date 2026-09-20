import os
import queue
import threading
import time
import unittest
from unittest.mock import Mock, patch

from dwm.storage.settings import Settings


@unittest.skipUnless(os.name == "nt", "Windows application")
from dwm.app import _StreamDeckRequest


class ShutdownUITests(unittest.TestCase):
    def test_shutdown_keeps_tk_running_while_service_waits_and_is_idempotent(self):
        from dwm.app import WindowManagerApp
        app = Mock()
        app.settings = Settings()
        app._stop_event = threading.Event()
        entered, release = threading.Event(), threading.Event()
        ui_thread = threading.get_ident()

        def stop_bridge():
            self.assertNotEqual(threading.get_ident(), ui_thread)
            entered.set()
            if not release.wait(5):
                raise AssertionError("test did not release service")

        app.streamdeck_bridge.stop.side_effect = stop_bridge
        app.hotkeys.stop.side_effect = RuntimeError("listener already stopped")
        try:
            with patch("dwm.app.save_settings"):
                WindowManagerApp.on_close(app, force=True)
                self.assertTrue(entered.wait(2))
                app.root.destroy.assert_not_called()
                callback = app.root.after.call_args.args[1]
                callback()
                app.root.destroy.assert_not_called()
                self.assertEqual(app.root.after.call_count, 2)
                WindowManagerApp.on_close(app, force=True)
                self.assertEqual(app.root.after.call_count, 2)
                release.set()
                # Poll just as Tk would, without relying on service scheduling.
                import time
                deadline = time.monotonic() + 3
                while not app.root.destroy.called and time.monotonic() < deadline:
                    callback()
                    time.sleep(0.01)
                app.root.destroy.assert_called_once()
                app.tray.stop.assert_called_once()
                app.overlay_ui.close_all.assert_called_once()
        finally:
            release.set()

    def test_shutdown_cancels_rotation_and_answers_pending_streamdeck_request(self):
        from dwm.app import WindowManagerApp

        app = Mock()
        app.settings = Settings(minimize_to_tray=False)
        app._stop_event = threading.Event()
        app._refresh_inflight = False
        app._rotation_request_job = "rotation-job"
        app._pending_rotation_delta = 3
        app._queue = queue.Queue()
        response: "queue.Queue[dict[str, object]]" = queue.Queue(maxsize=1)
        request = _StreamDeckRequest(
            request_id="closing-request",
            command="rotate",
            payload={"direction": "forward"},
            deadline=time.monotonic() + 10,
            response_queue=response,
        )
        app._queue.put(("streamdeck", request))
        app.tray.is_running = False

        with patch("dwm.app.save_settings"):
            WindowManagerApp.on_close(app, force=True)

        result = response.get(timeout=1)
        self.assertEqual(result["error_code"], "closing")
        self.assertEqual(result["request_id"], "closing-request")
        self.assertEqual(app._pending_rotation_delta, 0)
        self.assertIsNone(app._rotation_request_job)
        app.root.after_cancel.assert_called_once_with("rotation-job")

    def test_normal_close_still_minimizes_when_requested(self):
        from dwm.app import WindowManagerApp
        app = Mock()
        app.settings = Settings(minimize_to_tray=True)
        app._stop_event = threading.Event()
        app.tray.is_running = True
        WindowManagerApp.on_close(app)
        app._hide_main_window.assert_called_once()
        self.assertFalse(app._stop_event.is_set())
        app.root.destroy.assert_not_called()
