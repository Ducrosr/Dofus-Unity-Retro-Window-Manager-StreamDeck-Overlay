from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dwm.services.streamdeck_installer import bundled_streamdeck_plugin_path, open_streamdeck_plugin


class StreamDeckInstallerTests(unittest.TestCase):
    def test_bundled_plugin_must_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "plugin.streamDeckPlugin"
            package.write_bytes(b"package")
            with patch("dwm.services.streamdeck_installer.resource_path", return_value=str(package)):
                self.assertEqual(bundled_streamdeck_plugin_path(), package)

    def test_bundled_plugin_reports_a_missing_package(self) -> None:
        with patch("dwm.services.streamdeck_installer.resource_path", return_value="missing.streamDeckPlugin"):
            with self.assertRaises(FileNotFoundError):
                bundled_streamdeck_plugin_path()

    def test_open_uses_the_registered_file_association(self) -> None:
        opened: list[str] = []
        with tempfile.TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "plugin.streamDeckPlugin"
            package.write_bytes(b"package")

            result = open_streamdeck_plugin(package, opener=opened.append)

        self.assertEqual(result, package)
        self.assertEqual(opened, [str(package)])


if __name__ == "__main__":
    unittest.main()
