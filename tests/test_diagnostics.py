from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from dwm.services.diagnostics import build_diagnostic_report, format_activity, read_packaged_plugin_version


class DiagnosticsTests(unittest.TestCase):
    def test_packaged_plugin_version_is_read_from_the_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package = Path(temporary_directory) / "plugin.streamDeckPlugin"
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr(
                    "com.remyducros.dofuswindowmanager.sdPlugin/manifest.json",
                    json.dumps({"Version": "0.4.0.0"}),
                )

            self.assertEqual(read_packaged_plugin_version(package), "0.4.0.0")

    def test_activity_age_is_human_readable(self) -> None:
        self.assertEqual(format_activity(None, now=100), "aucune requête reçue")
        self.assertEqual(format_activity(95, now=100), "il y a 5 s")
        self.assertEqual(format_activity(0, now=125), "il y a 2 min")

    def test_report_contains_named_values(self) -> None:
        report = build_diagnostic_report([("Plugin", "0.4.0"), ("Fenêtres", 8)])

        self.assertIn("Plugin: 0.4.0", report)
        self.assertIn("Fenêtres: 8", report)


if __name__ == "__main__":
    unittest.main()
