import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from threading import Event
from unittest.mock import Mock, patch
from dwm.ui_update_download import UpdateDownloadDialog

from dwm.services.update_download import (
    DownloadAsset, OfficialRedirectHandler, download_asset, release_assets,
)
from dwm.services.update_checker import OFFICIAL_REPOSITORY, select_latest_release


class UpdateDownloadTests(unittest.TestCase):
    def setUp(self):
        self.data = b"MZ-example-executable"
        self.url = f"https://github.com/{OFFICIAL_REPOSITORY}/releases/download/v3.0.0/DofusWindowManager.exe"
        self.raw = dict(name="DofusWindowManager.exe", browser_download_url=self.url,
                        size=len(self.data), digest="sha256:" + hashlib.sha256(self.data).hexdigest())
        self.asset = release_assets("v3.0.0", [self.raw])[0]

    def test_selection_requires_official_url_digest_size_and_unique_name(self):
        for changes in ({"browser_download_url": "https://example.com/a.exe"}, {"digest": None},
                        {"size": -1}, {"size": True}, {"digest": "sha256:bad"}):
            self.assertEqual(release_assets("v3.0.0", [self.raw | changes]), ())
        self.assertEqual(release_assets("v3.0.0", [self.raw, self.raw]), ())
        selected = select_latest_release([dict(tag_name="v3.0.0", assets=[self.raw])],
                                         include_prereleases=False)
        self.assertEqual(selected[0].assets, (self.asset,))

    def test_download_verifies_without_overwriting_existing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            original = Path(folder) / self.asset.name
            original.write_bytes(b"old")
            path = download_asset(self.asset, Path(folder), Event(), lambda *args: None,
                                  opener=lambda *args, **kwargs: io.BytesIO(self.data))
            self.assertEqual(path.read_bytes(), self.data)
            self.assertEqual(original.read_bytes(), b"old")
            self.assertFalse(list(Path(folder).rglob("*.part")))

    def test_corrupt_short_oversized_and_network_failure_leave_no_file(self):
        with tempfile.TemporaryDirectory() as folder:
            for payload in (b"x" * len(self.data), self.data[:-1], self.data + b"x"):
                with self.assertRaises(ValueError):
                    download_asset(self.asset, Path(folder), Event(), lambda *args: None,
                                   opener=lambda *args, payload=payload, **kwargs: io.BytesIO(payload))
                self.assertEqual(list(Path(folder).iterdir()), [])
            def failure(*args, **kwargs):
                raise OSError("offline")
            with self.assertRaises(OSError):
                download_asset(self.asset, Path(folder), Event(), lambda *args: None, opener=failure)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_cancellation_cleans_partial_file(self):
        cancel = Event()
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(InterruptedError):
                download_asset(self.asset, Path(folder), cancel, lambda *args: cancel.set(),
                               opener=lambda *args, **kwargs: io.BytesIO(self.data))
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_untrusted_redirect_and_asset_rejected_before_network(self):
        for url in ("http://github.com/a", "https://github.com.evil.test/a",
                    "https://user@github.com/a", "https://example.com/a"):
            with self.assertRaises(ValueError):
                OfficialRedirectHandler().redirect_request(None, None, 302, "", {}, url)
        asset = DownloadAsset(self.asset.name, self.url.replace("v3.0.0", "../other"),
                              self.asset.size, self.asset.sha256)
        with self.assertRaises(ValueError):
            download_asset(asset, Path("."), Event(), lambda *args: None)

    def test_installer_requires_confirmation_and_rechecks_saved_file(self):
        dialog = object.__new__(UpdateDownloadDialog)
        dialog.status = Mock()
        dialog.button = Mock()
        dialog.window = Mock()
        dialog.cancel = Event()
        dialog.asset = DownloadAsset("DofusWindowManager-Setup.exe", self.url,
                                     len(self.data), hashlib.sha256(self.data).hexdigest())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "installer.exe"
            path.write_bytes(self.data)
            with patch("dwm.ui_update_download.messagebox") as messages, patch(
                    "dwm.ui_update_download.os.startfile", create=True) as launch:
                messages.askyesno.return_value = False
                dialog.finish(path)
                launch.assert_not_called()
                messages.askyesno.return_value = True
                path.write_bytes(b"modified")
                dialog.finish(path)
                launch.assert_not_called()
                messages.showwarning.assert_called_once()
                path.write_bytes(self.data)
                dialog.finish(path)
                launch.assert_called_once_with(str(path))

    def test_portable_is_never_executed(self):
        dialog = object.__new__(UpdateDownloadDialog)
        dialog.status = Mock()
        dialog.button = Mock()
        dialog.window = Mock()
        dialog.cancel = Event()
        dialog.asset = self.asset
        with patch("dwm.ui_update_download.messagebox") as messages, patch(
                "dwm.ui_update_download.os.startfile", create=True) as launch:
            dialog.finish(Path("portable.exe"))
            messages.showinfo.assert_called_once()
            launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
