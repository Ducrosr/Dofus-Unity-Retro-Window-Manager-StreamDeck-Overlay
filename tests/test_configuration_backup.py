from __future__ import annotations

import unittest

from dwm.services.configuration_backup import build_configuration_backup, parse_configuration_backup
from dwm.storage.profiles import Profile
from dwm.storage.settings import Settings


class ConfigurationBackupTests(unittest.TestCase):
    def test_backup_round_trip_preserves_settings_profiles_and_session(self) -> None:
        profile = Profile(
            name="Équipe",
            order=["Nealla", "Korra"],
            aliases={"Nealla": "Terre"},
            created_at="2026-08-22T00:00:00",
            updated_at="2026-08-22T00:00:00",
        )
        backup = build_configuration_backup(
            Settings(start_with_windows=True),
            [profile],
            active_profile="Équipe",
            current_order=["Korra", "Nealla"],
            current_aliases={"Nealla": "Terre", "Korra": ""},
            app_version="2.18.0",
        )

        settings, profiles, session = parse_configuration_backup(backup)

        self.assertTrue(settings.start_with_windows)
        self.assertEqual(profiles[0].aliases, {"Nealla": "Terre"})
        self.assertEqual(session["active_profile"], "Équipe")
        self.assertEqual(session["order"], ["Korra", "Nealla"])
        self.assertEqual(session["aliases"], {"Nealla": "Terre"})

    def test_unrelated_json_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "sauvegarde Dofus Window Manager"):
            parse_configuration_backup({"format": "other"})


if __name__ == "__main__":
    unittest.main()
