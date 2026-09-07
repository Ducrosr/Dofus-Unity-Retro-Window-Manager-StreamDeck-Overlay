import os
import unittest
from contextlib import ExitStack
from unittest.mock import Mock, patch

from dwm.storage.settings import Settings
from dwm.services.update_checker import UpdateCheckResult, ReleaseInfo


@unittest.skipUnless(os.name == "nt", "Windows application UI")
class UpdatePresetUITests(unittest.TestCase):
    def test_result_is_delivered_without_processing_general_queue(self):
        from dwm.app import WindowManagerApp
        app = Mock()
        app.settings = Settings()
        app._stop_event.is_set.return_value = False
        app._update_check_inflight = False
        result = UpdateCheckResult("v2.20.0", None, False)
        with patch("dwm.app.check_for_update", return_value=result), patch("dwm.app.threading.Thread") as thread:
            thread.side_effect = lambda **kw: Mock(start=kw["target"])
            WindowManagerApp._start_update_check(app, manual=True)
            app.root.after.call_args.args[1]()
        app._finish_update_check.assert_called_once()
        self.assertIs(app._finish_update_check.call_args.kwargs["result"], result)
        app._queue.put.assert_not_called()

    def test_timeout_reports_error_and_stops_polling(self):
        from dwm.app import WindowManagerApp
        app = Mock()
        app.settings = Settings()
        app._stop_event.is_set.return_value = False
        app._update_check_inflight = False
        with patch("dwm.app.threading.Thread"), patch("dwm.app.time.monotonic", side_effect=[0, 21]):
            WindowManagerApp._start_update_check(app, manual=True)
            app.root.after.call_args.args[1]()
        self.assertTrue(app._finish_update_check.call_args.kwargs["error"])
        self.assertEqual(app.root.after.call_count, 1)

    def test_manual_results_always_provide_feedback(self):
        from dwm.app import WindowManagerApp
        release = ReleaseInfo("v3.0.0", "v3.0.0", "", "", False)
        for result, error, expected in [
            (UpdateCheckResult("v2.0.0", None, False), "", "info"),
            (UpdateCheckResult("v2.0.0", release, True), "", "offer"),
            (None, "offline", "warning"),
        ]:
            app = Mock()
            app.settings = Settings()
            with patch("dwm.app.save_settings"), patch("dwm.app.messagebox") as messages:
                WindowManagerApp._finish_update_check(app, manual=True, result=result, error=error, checked_at="")
                if expected == "offer":
                    app._offer_official_release.assert_called_once_with(release)
                elif expected == "info":
                    messages.showinfo.assert_called_once()
                else:
                    messages.showwarning.assert_called_once()

    def test_each_preset_replaces_preview_without_saving_settings(self):
        from dwm.app import WindowManagerApp
        app = Mock()
        app.settings = Settings()
        saved = app.settings.to_dict()
        app.display_simulation_window = None
        with ExitStack() as stack:
            for name in ("Toplevel", "TtkFrame", "TtkLabel", "TtkButton", "resolved_theme_palette"):
                stack.enter_context(patch("dwm.app." + name))
            overlay = stack.enter_context(patch("dwm.app.OverlayUI"))
            renderings = []
            for preset in ("minimal", "balanced", "complete"):
                WindowManagerApp.open_display_simulation(app, preset_id=preset)
                renderings.append(overlay.return_value.configure_persistent.call_args.kwargs)
            self.assertFalse(renderings[0]["show_title"])
            self.assertTrue(renderings[1]["show_portrait"])
            self.assertFalse(renderings[1]["show_badge"])
            self.assertTrue(renderings[2]["show_badge"])
            self.assertTrue(renderings[2]["show_reorder_buttons"])
            self.assertEqual(overlay.return_value.close_all.call_count, 2)
        self.assertEqual(app.settings.to_dict(), saved)
