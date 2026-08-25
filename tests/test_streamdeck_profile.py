from __future__ import annotations

import base64
import json
import re
import unittest
import uuid
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = PROJECT_ROOT / "streamdeck-plugin" / "com.remyducros.dofuswindowmanager.sdPlugin"
PROFILE_PATH = PLUGIN_ROOT / "profiles" / "DofusWindowManager.streamDeckProfile"
EXPECTED_PROFILES = {
    "profiles/DofusWindowManager": (0, 5, 3, set(range(1, 9))),
    "profiles/DofusWindowManagerMini": (1, 3, 2, set(range(1, 5))),
    "profiles/DofusWindowManagerXL": (2, 8, 4, set(range(1, 9))),
    "profiles/DofusWindowManagerPlus": (7, 4, 2, set(range(1, 7))),
    "profiles/DofusWindowManagerNeo": (9, 4, 2, set(range(1, 7))),
}


class StreamDeckProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with ZipFile(PROFILE_PATH) as archive:
            cls.profile_entries = archive.namelist()
            manifest_names = [name for name in cls.profile_entries if name.endswith("manifest.json")]
            cls.manifest_by_name = {name: json.loads(archive.read(name)) for name in manifest_names}
            cls.manifests = list(cls.manifest_by_name.values())

        cls.profile_manifest = next(manifest for manifest in cls.manifests if manifest.get("Version") == "2.0")
        cls.action_manifest = next(
            manifest
            for manifest in cls.manifests
            if any(controller.get("Actions") for controller in manifest.get("Controllers", []))
        )
        cls.actions = cls.action_manifest["Controllers"][0]["Actions"]

    def test_page_ids_resolve_to_their_internal_profile_directories(self) -> None:
        roots = {PurePosixPath(name).parts[0] for name in self.profile_entries}
        self.assertEqual(len(roots), 1)
        root = roots.pop()
        self.assertRegex(root, re.compile(r"^[0-9A-F]{8}(?:-[0-9A-F]{4}){3}-[0-9A-F]{12}\.sdProfile$"))

        pages = self.profile_manifest["Pages"]
        current_name = self._encoded_page_directory(pages["Current"])
        default_name = self._encoded_page_directory(pages["Default"])
        current_manifest = self.manifest_by_name[f"{root}/Profiles/{current_name}/manifest.json"]
        default_manifest = self.manifest_by_name[f"{root}/Profiles/{default_name}/manifest.json"]

        self.assertTrue(any(controller.get("Actions") for controller in current_manifest["Controllers"]))
        self.assertFalse(any(controller.get("Actions") for controller in default_manifest["Controllers"]))

    @staticmethod
    def _encoded_page_directory(page_id: str) -> str:
        encoded = base64.b32hexencode(uuid.UUID(page_id).bytes).decode("ascii").rstrip("=")
        return encoded.translate(str.maketrans({"U": "V", "V": "W"})) + "Z"

    def test_plugin_declares_editable_auto_installed_profiles_for_each_device(self) -> None:
        plugin_manifest = json.loads((PLUGIN_ROOT / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(
            {
                profile["Name"]: profile["DeviceType"]
                for profile in plugin_manifest["Profiles"]
            },
            {
                name: expected[0]
                for name, expected in EXPECTED_PROFILES.items()
            },
        )
        for profile in plugin_manifest["Profiles"]:
            self.assertFalse(profile["Readonly"])
            self.assertFalse(profile["DontAutoSwitchWhenInstalled"])
            self.assertTrue(profile["AutoInstall"])
        self.assertEqual(self.profile_manifest["Name"], "Dofus Window Manager — 15 touches")
        self.assertEqual(self.profile_manifest["Device"]["Model"], "20GAA9901")

    def test_each_declared_profile_exists_and_fits_its_device_grid(self) -> None:
        for profile_name, (_device_type, columns, rows, expected_slots) in EXPECTED_PROFILES.items():
            profile_path = PLUGIN_ROOT / f"{profile_name}.streamDeckProfile"
            self.assertTrue(profile_path.is_file(), profile_path)
            with ZipFile(profile_path) as archive:
                manifests = [
                    json.loads(archive.read(name))
                    for name in archive.namelist()
                    if name.endswith("manifest.json")
                ]
            root_manifest = next(manifest for manifest in manifests if manifest.get("Version") == "2.0")
            action_manifest = next(
                manifest
                for manifest in manifests
                if any(controller.get("Actions") for controller in manifest.get("Controllers", []))
            )
            actions = action_manifest["Controllers"][0]["Actions"]
            slots = {
                int(action["Settings"]["slot"])
                for action in actions.values()
                if action["UUID"] == "com.remyducros.dofuswindowmanager.character"
            }
            self.assertEqual(slots, expected_slots)
            self.assertTrue(root_manifest["Device"]["Model"])
            for coordinate in actions:
                column, row = (int(value) for value in coordinate.split(","))
                self.assertGreaterEqual(column, 0)
                self.assertLess(column, columns)
                self.assertGreaterEqual(row, 0)
                self.assertLess(row, rows)

    def test_profile_matches_the_requested_three_by_five_layout(self) -> None:
        expected = {
            "0,0": "com.remyducros.dofuswindowmanager.move-up",
            "1,0": "com.remyducros.dofuswindowmanager.character",
            "2,0": "com.remyducros.dofuswindowmanager.character",
            "3,0": "com.remyducros.dofuswindowmanager.character",
            "4,0": "com.remyducros.dofuswindowmanager.character",
            "0,1": "com.remyducros.dofuswindowmanager.move-down",
            "0,2": "com.remyducros.dofuswindowmanager.launch",
            "1,1": "com.remyducros.dofuswindowmanager.character",
            "2,1": "com.remyducros.dofuswindowmanager.character",
            "3,1": "com.remyducros.dofuswindowmanager.character",
            "4,1": "com.remyducros.dofuswindowmanager.character",
            "1,2": "com.remyducros.dofuswindowmanager.toggle-ignore",
            "2,2": "com.remyducros.dofuswindowmanager.refresh",
            "3,2": "com.remyducros.dofuswindowmanager.previous",
            "4,2": "com.remyducros.dofuswindowmanager.next",
        }

        self.assertEqual({coordinate: action["UUID"] for coordinate, action in self.actions.items()}, expected)

    def test_eight_character_buttons_have_slots_and_default_text_lines(self) -> None:
        character_actions = [
            action
            for action in self.actions.values()
            if action["UUID"] == "com.remyducros.dofuswindowmanager.character"
        ]

        self.assertEqual({action["Settings"]["slot"] for action in character_actions}, {str(i) for i in range(1, 9)})
        for action in character_actions:
            self.assertEqual(
                action["Settings"],
                {
                    "accentColor": "auto",
                    "aliasLine": "4",
                    "classLine": "3",
                    "display": "name",
                    "nameLine": "2",
                    "positionLine": "1",
                    "slot": action["Settings"]["slot"],
                },
            )


if __name__ == "__main__":
    unittest.main()
