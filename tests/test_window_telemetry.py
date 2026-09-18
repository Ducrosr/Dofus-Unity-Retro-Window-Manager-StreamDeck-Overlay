from __future__ import annotations

import unittest

from dwm.services.window_telemetry import (
    RectSnapshot,
    WindowTelemetry,
    encode_obs_window_selector,
)


class WindowTelemetryTests(unittest.TestCase):
    def test_obs_selector_matches_obs_window_helper_encoding(self) -> None:
        value = encode_obs_window_selector(
            "Name #1: Cra",
            "UnityWndClass",
            "Dofus.exe",
        )

        self.assertEqual(
            value,
            "Name #221#3A Cra:UnityWndClass:Dofus.exe",
        )

    def test_session_and_geometry_are_exported_with_derived_obs_fields(self) -> None:
        snapshot = WindowTelemetry(
            hwnd=123,
            session_id="456:789:123",
            game_mode="unity",
            title="Nat - Eniripsa - Dofus",
            window_class="UnityWndClass",
            pseudo="Nat",
            character_class="Eniripsa",
            pid=456,
            process_path=r"C:\Games\Dofus\Dofus.exe",
            process_name="Dofus.exe",
            window_rect=RectSnapshot(10, 20, 1930, 1100),
        )

        data = snapshot.to_dict()

        self.assertEqual(data["session_id"], "456:789:123")
        self.assertEqual(data["window_rect"]["width"], 1920)
        self.assertEqual(data["window_rect"]["height"], 1080)
        self.assertEqual(data["obs_executable"], "Dofus.exe")
        self.assertEqual(
            data["obs_window_selector"],
            "Nat - Eniripsa - Dofus:UnityWndClass:Dofus.exe",
        )


if __name__ == "__main__":
    unittest.main()
