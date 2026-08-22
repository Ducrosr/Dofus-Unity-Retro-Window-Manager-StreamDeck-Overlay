from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dwm.services.app_launcher import build_launcher_descriptor, register_current_launcher


class AppLauncherTests(unittest.TestCase):
    def test_packaged_application_launches_its_executable_directly(self) -> None:
        descriptor = build_launcher_descriptor(
            frozen=True,
            executable=Path("C:/Apps/DofusWindowManager/DofusWindowManager.exe"),
            app_dir=Path("C:/Apps/DofusWindowManager"),
        )

        self.assertEqual(descriptor["version"], 1)
        self.assertTrue(str(descriptor["executable"]).endswith("DofusWindowManager.exe"))
        self.assertEqual(descriptor["arguments"], ["--use-saved-mode"])

    def test_source_application_launches_main_with_the_current_python(self) -> None:
        descriptor = build_launcher_descriptor(
            frozen=False,
            executable=Path("C:/Project/.venv/Scripts/python.exe"),
            app_dir=Path("C:/Project"),
        )

        self.assertTrue(str(descriptor["executable"]).endswith("python.exe"))
        self.assertTrue(str(descriptor["arguments"][0]).endswith("main.py"))
        self.assertEqual(descriptor["arguments"][1], "--use-saved-mode")
        self.assertTrue(str(descriptor["working_directory"]).endswith("Project"))

    def test_registration_writes_the_descriptor_in_the_data_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            descriptor = {
                "version": 1,
                "executable": "C:/DWM.exe",
                "arguments": [],
                "working_directory": "C:/",
            }
            with patch("dwm.services.app_launcher.build_launcher_descriptor", return_value=descriptor):
                path = register_current_launcher(root)

            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), descriptor)
            self.assertFalse(path.with_suffix(".tmp").exists())


if __name__ == "__main__":
    unittest.main()
