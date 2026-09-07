from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tests import test_app_order_sync
from dwm.storage.profiles import Profile, load_profile, save_profile
from dwm.storage.settings import Settings, normalize_profile_overlays


class ProfileOverlayTests(unittest.TestCase):
    def test_legacy_profile_does_not_change_display(self):
        settings = Settings(rotation_overlay_orientation="horizontal")
        profile = Profile.from_dict({"name": "Legacy", "order": []})
        self.assertFalse(settings.apply_profile_overlay(profile.overlay_by_game_mode, "unity"))
        self.assertEqual(settings.rotation_overlay_orientation, "horizontal")

    def test_normalization_filters_non_overlay_fields_and_invalid_modes(self):
        result = normalize_profile_overlays({
            "unity": {"theme": "retro", "hotkey_scope": "game", "rotation_overlay_width": 9000,
                      "rotation_overlay_x": float("inf"), "rotation_overlay_orientation": "invalid"},
            "retro": [], "other": {"rotation_overlay_width": 500},
        })
        self.assertEqual(result, {"unity": {"rotation_overlay_width": 1800,
                                          "rotation_overlay_x": 24,
                                          "rotation_overlay_orientation": "vertical"}})

    def test_roundtrip_preserves_both_modes_and_independent_snapshots(self):
        settings = Settings(rotation_overlay_orientation="horizontal")
        profile = Profile("Team", [], {}, "", "", overlay_by_game_mode={
            "unity": settings.overlay_preferences_snapshot(),
            "retro": {"rotation_overlay_width": 450},
        })
        original_layout = dict(settings.rotation_overlay_layout)
        settings.rotation_overlay_layout["line1"] = "alias"
        with tempfile.TemporaryDirectory() as directory:
            save_profile(Path(directory), profile)
            loaded = load_profile(Path(directory), "Team")
        self.assertEqual(loaded.overlay_by_game_mode["unity"]["rotation_overlay_layout"], original_layout)
        self.assertTrue(settings.apply_profile_overlay(loaded.overlay_by_game_mode, "retro"))
        self.assertEqual(settings.rotation_overlay_width, 450)
        self.assertEqual(loaded.overlay_by_game_mode["unity"]["rotation_overlay_orientation"], "horizontal")

    def make_app(self):
        app = test_app_order_sync.AppOrderSyncTests().make_app()
        app.settings = Settings()
        app.character_visuals = {}
        app._legacy_character_visuals = {}
        app.profile_overlay_var = Mock()
        app._apply_display_preferences = Mock()
        return app

    def test_activation_applies_overlay_before_publishing_and_respects_mode(self):
        app = self.make_app()
        profile = Profile("Team", ["Nat", "Nealla"], {}, "", "", visuals={}, overlay_by_game_mode={
            "unity": {"rotation_overlay_orientation": "horizontal", "rotation_overlay_show_title": False},
            "retro": {"rotation_overlay_orientation": "vertical"},
        })
        app._activate_profile(profile)
        app._apply_display_preferences.assert_called_once()
        app.profile_overlay_var.set.assert_called_with(True)
        self.assertEqual(app.settings.rotation_overlay_orientation, "horizontal")
        self.assertFalse(app.settings.rotation_overlay_show_title)
        self.assertEqual(app._managed_order[:2], [102, 101])
        self.assertEqual(app.settings.display_by_game_mode["unity"]["rotation_overlay_orientation"], "horizontal")
        app.game_mode = "retro"
        app._activate_profile(profile)
        self.assertEqual(app.settings.rotation_overlay_orientation, "vertical")
        self.assertEqual(app.settings.display_by_game_mode["unity"]["rotation_overlay_orientation"], "horizontal")

    def test_unlinked_profile_keeps_current_overlay(self):
        app = self.make_app()
        app.settings.rotation_overlay_width = 600
        app._activate_profile(Profile("Legacy", [], {}, "", "", visuals={}))
        self.assertEqual(app.settings.rotation_overlay_width, 600)
        app.profile_overlay_var.set.assert_called_with(False)
        app._apply_display_preferences.assert_not_called()

    def test_saving_can_detach_and_reattach_without_losing_other_mode(self):
        app = self.make_app()
        app.selected_profile = Mock()
        app.selected_profile.get.return_value = "Team"
        app._get_profiles = Mock(return_value=["Team"])
        app._create_configuration_snapshot = Mock()
        app._refresh_profile_combo = Mock()
        app._log = Mock()
        app.root = Mock()
        with tempfile.TemporaryDirectory() as directory:
            app.dirs = {"profiles": Path(directory)}
            app.settings_path = Path(directory) / "settings.json"
            save_profile(Path(directory), Profile("Team", [], {}, "", "", overlay_by_game_mode={
                "unity": {"rotation_overlay_width": 400}, "retro": {"rotation_overlay_width": 500},
            }))
            with patch("dwm.app.simpledialog.askstring", return_value="Team"), patch("dwm.app.messagebox.askyesno", return_value=True):
                app.profile_overlay_var.get.return_value = False
                app.save_profile_dialog()
                self.assertEqual(load_profile(Path(directory), "Team").overlay_by_game_mode,
                                 {"retro": {"rotation_overlay_width": 500}})
                app.profile_overlay_var.get.return_value = True
                app.settings.rotation_overlay_width = 700
                app.save_profile_dialog()
            overlays = load_profile(Path(directory), "Team").overlay_by_game_mode
            self.assertEqual(overlays["unity"]["rotation_overlay_width"], 700)
            self.assertEqual(overlays["retro"]["rotation_overlay_width"], 500)


if __name__ == "__main__":
    unittest.main()
