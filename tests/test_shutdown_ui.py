import os
import threading
import unittest
from unittest.mock import Mock, patch

from dwm.storage.settings import Settings, UnsupportedSettingsSchemaError


@unittest.skipUnless(os.name == "nt", "Windows application")
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

    def test_close_continues_when_settings_cannot_be_written(self):
        from dwm.app import WindowManagerApp

        app = Mock()
        app.settings = Settings()
        app._stop_event = threading.Event()
        app._rotation_request_job = "rotation-job"
        app._pending_rotation_delta = 2
        app.tray.is_running = False
        finished_callbacks = []

        def schedule(_delay, callback):
            finished_callbacks.append(callback)
            return "job"

        app.root.after.side_effect = schedule

        with patch(
            "dwm.app.save_settings",
            side_effect=UnsupportedSettingsSchemaError("future schema"),
        ):
            WindowManagerApp.on_close(app, force=True)

        self.assertTrue(app._stop_event.is_set())
        self.assertEqual(app._pending_rotation_delta, 0)
        app.root.after_cancel.assert_called_once_with("rotation-job")
        app.overlay_ui.close_all.assert_called_once_with()

        # Service shutdown remains asynchronous and must still be able to
        # complete even though persistence was rejected.
        for _ in range(100):
            if app.tray.stop.called:
                break
            threading.Event().wait(0.01)
        self.assertTrue(app.tray.stop.called)

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
