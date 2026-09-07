import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dwm.services.session_recovery import SessionRecovery


class SessionRecoveryTests(unittest.TestCase):
    def test_clean_exit_does_not_trigger_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            first = SessionRecovery(Path(directory))
            self.assertTrue(first.begin())
            self.assertFalse(first.previous_interruption)
            first.complete()
            first.close()
            second = SessionRecovery(Path(directory))
            try:
                self.assertTrue(second.begin())
                self.assertFalse(second.previous_interruption)
                second.complete()
            finally:
                second.close()

    def test_abrupt_process_exit_releases_lock_but_preserves_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            code = ("import os,sys; from pathlib import Path; "
                    "from dwm.services.session_recovery import SessionRecovery; "
                    "session=SessionRecovery(Path(sys.argv[1])); "
                    "assert session.begin(); os._exit(17)")
            process = subprocess.run([sys.executable, "-c", code, directory], timeout=15)
            self.assertEqual(process.returncode, 17)
            resumed = SessionRecovery(Path(directory))
            try:
                self.assertTrue(resumed.begin())
                self.assertTrue(resumed.previous_interruption)
                resumed.complete()
            finally:
                resumed.close()

    def test_live_session_is_not_reported_as_interrupted_or_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            active = SessionRecovery(Path(directory))
            self.assertTrue(active.begin())
            try:
                code = ("import sys; from pathlib import Path; "
                        "from dwm.services.session_recovery import SessionRecovery; "
                        "session=SessionRecovery(Path(sys.argv[1])); "
                        "assert not session.begin(); "
                        "assert not session.previous_interruption; session.complete(); session.close()")
                subprocess.run([sys.executable, "-c", code, directory], timeout=15, check=True)
                self.assertTrue(active.marker.exists())
                active.complete()
            finally:
                active.close()

    def test_marker_write_failure_releases_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            first = SessionRecovery(Path(directory))
            with patch("dwm.services.session_recovery.atomic_write_text", side_effect=OSError):
                with self.assertRaises(OSError):
                    first.begin()
            self.assertIsNone(first._lock)
            second = SessionRecovery(Path(directory))
            try:
                self.assertTrue(second.begin())
                second.complete()
            finally:
                second.close()

    @unittest.skipUnless(os.name == "nt", "Windows application")
    def test_support_export_requires_acceptance_and_running_application(self):
        from dwm.app import WindowManagerApp
        app = Mock()
        app._stop_event.is_set.return_value = False
        with patch("dwm.app.messagebox.askyesno", return_value=False):
            WindowManagerApp.offer_interrupted_session_diagnostic(app)
        app.export_support_bundle.assert_not_called()
        with patch("dwm.app.messagebox.askyesno", return_value=True):
            WindowManagerApp.offer_interrupted_session_diagnostic(app)
        app.export_support_bundle.assert_called_once()
        app._stop_event.is_set.return_value = True
        with patch("dwm.app.messagebox.askyesno") as prompt:
            WindowManagerApp.offer_interrupted_session_diagnostic(app)
        prompt.assert_not_called()


if __name__ == "__main__":
    unittest.main()
