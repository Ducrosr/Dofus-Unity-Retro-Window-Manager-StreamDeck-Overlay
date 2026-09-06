from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from tests import test_app_order_sync
from dwm.services.configuration_backup import build_configuration_backup
from dwm.services.configuration_diff import ConfigurationChange, compare_configuration, compare_profiles
from dwm.services.character_roster import CharacterRoster
from dwm.storage.profiles import Profile, save_profile
from dwm.storage.settings import Settings
from dwm.ui_configuration_preview import readable_path, readable_value


def profile(name="Team", **kwargs):
    return Profile(name, ["A", "B"], {}, "", "", **kwargs)


class ConfigurationDiffTests(unittest.TestCase):
    def test_profiles_compare_content_ignore_timestamps_and_keep_unrelated_profiles(self):
        current = profile()
        incoming = copy.deepcopy(current)
        incoming.updated_at = "later"
        changes, retained = compare_profiles([current, profile("Other")], [incoming])
        self.assertEqual((changes, retained), ([], 1))
        incoming.order.reverse()
        incoming.aliases["updated_at"] = "Character alias"
        changes, _ = compare_profiles([current], [incoming])
        self.assertEqual({item.path for item in changes}, {("Team", "order"), ("Team", "character_slots"), ("Team", "aliases", "updated_at")})
        self.assertEqual(current.order, ["A", "B"])

    def test_added_profile_and_removed_alias_are_visible(self):
        current, incoming = profile(), profile()
        current.aliases = {"A": "Tank"}
        changes, _ = compare_profiles([current], [incoming, profile("New")])
        self.assertTrue(any(item.path == ("Team", "aliases", "A") and item.before == "Tank" and item.after is None for item in changes))
        self.assertTrue(any(item.path == ("New",) and item.before is None for item in changes))

    def test_colliding_windows_filenames_are_rejected(self):
        for names in [("TEAM", "team"), ("A/B", "A:B")]:
            with self.subTest(names=names), self.assertRaises(ValueError):
                compare_profiles([], [profile(name) for name in names])
        changes, retained = compare_profiles([profile("TEAM")], [profile("team")])
        self.assertEqual(retained, 0)
        self.assertEqual(changes[0].path, ("team", "name"))

    def test_settings_session_and_overlay_are_compared_without_mutation(self):
        before = Settings()
        after = Settings(start_with_windows=True)
        old_profile = profile(overlay_by_game_mode={"unity": {"rotation_overlay_width": 300}})
        new_profile = profile(overlay_by_game_mode={"unity": {"rotation_overlay_width": 600}})
        original = copy.deepcopy(old_profile.to_dict())
        changes, _ = compare_configuration(before.to_dict(), after.to_dict(), [old_profile], [new_profile],
                                           {"order": ["A", "B"]}, {"order": ["B", "A"]})
        self.assertEqual({item.section for item in changes}, {"Paramètres", "Profils", "Session actuelle"})
        self.assertEqual(old_profile.to_dict(), original)
        self.assertFalse(before.start_with_windows)

    def test_values_hide_image_payload_and_keep_literal_names(self):
        self.assertNotIn("base64", readable_value({"portrait": "data:image/png;base64,AAAA"}))
        change = ConfigurationChange("Profils", ("theme", "aliases", "my_character"), "A", "B")
        self.assertIn("theme / Alias / my_character", readable_path(change))


class ConfigurationImportTests(unittest.TestCase):
    def make_app(self, directory):
        app = test_app_order_sync.AppOrderSyncTests().make_app()
        app.settings = Settings()
        app.root = Mock()
        app.dirs = {"profiles": Path(directory)}
        app._roster = CharacterRoster(order=["A", "B"], slots=["A", "B"])
        app._active_profile_name = "Team"
        app._create_configuration_snapshot = Mock(return_value=object())
        app._apply_restored_configuration = Mock()
        app._refresh_profile_combo = Mock()
        app.selected_profile = Mock()
        app._log = Mock()
        return app

    def backup(self):
        return build_configuration_backup(Settings(start_with_windows=True), [profile()],
            active_profile="Team", current_order=["B", "A"], current_aliases={}, app_version="test")

    def test_cancel_restore_leaves_memory_and_files_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.make_app(directory)
            original = copy.deepcopy(app.settings.to_dict())
            with patch("dwm.app.confirm_configuration_changes", return_value=False) as preview:
                self.assertFalse(app._restore_configuration_data(self.backup(), source="test", parent=app.root))
            preview.assert_called_once()
            app._create_configuration_snapshot.assert_not_called()
            app._apply_restored_configuration.assert_not_called()
            self.assertEqual(app.settings.to_dict(), original)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_restore_creates_snapshot_after_confirmation_before_application(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.make_app(directory)
            calls = []
            app._create_configuration_snapshot.side_effect = lambda _reason: calls.append("snapshot") or object()
            app._apply_restored_configuration.side_effect = lambda *_a, **_kw: calls.append("apply")
            with patch("dwm.app.confirm_configuration_changes", side_effect=lambda *_args: calls.append("preview") or True):
                self.assertTrue(app._restore_configuration_data(self.backup(), source="test", parent=app.root))
            self.assertEqual(calls, ["preview", "snapshot", "apply"])

    def test_failed_snapshot_blocks_restoration(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.make_app(directory)
            app._create_configuration_snapshot.return_value = None
            with patch("dwm.app.confirm_configuration_changes", return_value=True), patch("dwm.app.messagebox.showerror"):
                self.assertFalse(app._restore_configuration_data(self.backup(), source="test", parent=app.root))
            app._apply_restored_configuration.assert_not_called()

    def test_snapshot_uses_loaded_profile_instead_of_unloaded_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.make_app(directory)
            app._get_profiles = Mock(return_value=[])
            app.selected_profile.get.return_value = "Not loaded"
            app.auto_refresh_enabled = Mock()
            app.auto_refresh_enabled.get.return_value = True
            backup = app._build_current_configuration_backup()
            self.assertEqual(backup["current_session"]["active_profile"], "Team")
            self.assertEqual(backup["settings"]["last_profile"], "Team")

    def test_duplicate_targets_fail_before_preview_and_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.make_app(directory)
            backup = self.backup()
            backup["profiles"].append(profile("TEAM").to_dict())
            with patch("dwm.app.confirm_configuration_changes") as preview, patch("dwm.app.messagebox.showerror"):
                self.assertFalse(app._restore_configuration_data(backup, source="test", parent=app.root))
            preview.assert_not_called()
            app._create_configuration_snapshot.assert_not_called()

    def test_profile_import_cancel_then_accept_preserves_other_profiles(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as source:
            app = self.make_app(directory)
            save_profile(Path(directory), profile("Other"))
            path = Path(source) / "new.json"
            path.write_text(json.dumps(profile().to_dict()))
            with patch("dwm.app.filedialog.askopenfilename", return_value=str(path)), patch("dwm.app.confirm_configuration_changes", return_value=False):
                app.import_profile_json()
            self.assertFalse((Path(directory) / "Team.json").exists())
            app._create_configuration_snapshot.assert_not_called()
            with patch("dwm.app.filedialog.askopenfilename", return_value=str(path)), patch("dwm.app.confirm_configuration_changes", return_value=True):
                app.import_profile_json()
            self.assertTrue((Path(directory) / "Team.json").exists())
            self.assertTrue((Path(directory) / "Other.json").exists())
            app._create_configuration_snapshot.assert_called_once()


if __name__ == "__main__":
    unittest.main()
