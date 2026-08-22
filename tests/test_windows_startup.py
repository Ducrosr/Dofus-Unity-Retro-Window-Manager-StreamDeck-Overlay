from __future__ import annotations

import unittest
from pathlib import Path

from dwm.services.windows_startup import build_startup_command


class WindowsStartupTests(unittest.TestCase):
    def test_packaged_startup_uses_the_executable_and_minimized_mode(self) -> None:
        command = build_startup_command(
            frozen=True,
            executable=Path("C:/Program Files/DWM/DofusWindowManager.exe"),
            app_dir=Path("C:/Program Files/DWM"),
        )

        self.assertIn("DofusWindowManager.exe", command)
        self.assertIn("--use-saved-mode", command)
        self.assertIn("--minimized", command)

    def test_source_startup_uses_pythonw_and_main(self) -> None:
        command = build_startup_command(
            frozen=False,
            executable=Path("C:/Python314/python.exe"),
            app_dir=Path("C:/Projects/DWM"),
        )

        self.assertIn("pythonw.exe", command)
        self.assertIn("main.py", command)
        self.assertIn("--minimized", command)


if __name__ == "__main__":
    unittest.main()
