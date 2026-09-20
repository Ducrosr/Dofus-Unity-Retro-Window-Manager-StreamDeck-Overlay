from __future__ import annotations

import tempfile
import unittest
import pickle
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from dwm.storage.profiles import (
    PROFILE_SCHEMA_VERSION,
    Profile,
    ProfileSchemaTooNewError,
    list_profiles,
    load_profile,
    migrate_pickles,
    profile_backup_path,
    profile_path,
    save_profile,
)


class ProfileTests(unittest.TestCase):
    def test_profile_round_trip_and_safe_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profiles_dir = Path(tmp)
            now = datetime.now().isoformat(timespec="seconds")
            profile = Profile(
                name='Équipe: "Boune"',
                order=["Iop", "Eni"],
                aliases={"Iop": "Tank"},
                created_at=now,
                updated_at=now,
                visuals={"Iop": {"portrait": "", "badge": "ankama_force"}},
                game_mode="retro",
            )
            save_profile(profiles_dir, profile)

            expected_path = profile_path(profiles_dir, profile.name)
            self.assertTrue(expected_path.exists())
            self.assertNotIn(":", expected_path.name)
            self.assertEqual(list_profiles(profiles_dir), [profile.name])
            loaded = load_profile(profiles_dir, profile.name)

        self.assertEqual(loaded.name, profile.name)
        self.assertEqual(loaded.order, ["Iop", "Eni"])
        self.assertEqual(loaded.aliases, {"Iop": "Tank"})
        self.assertEqual(loaded.visuals, {"Iop": {"portrait": "", "badge": "ankama_force"}})
        self.assertEqual(loaded.game_mode, "retro")

    def test_legacy_profile_keeps_visuals_unspecified_for_migration(self) -> None:
        profile = Profile.from_dict(
            {
                "schema_version": 1,
                "name": "Ancien serveur",
                "order": ["Iop"],
                "aliases": {},
            }
        )

        self.assertIsNone(profile.visuals)
        self.assertEqual(profile.game_mode, "")

    def test_list_profiles_is_case_insensitive_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profiles_dir = Path(tmp)
            for name in ("zeta", "Alpha"):
                now = datetime.now().isoformat(timespec="seconds")
                save_profile(profiles_dir, Profile(name, [], {}, now, now))
            names = list_profiles(profiles_dir)

        self.assertEqual(names, ["Alpha", "zeta"])

    def test_failed_profile_replacement_preserves_previous_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profiles_dir = Path(tmp)
            now = datetime.now().isoformat(timespec="seconds")
            original = Profile("Équipe", ["Iop"], {}, now, now)
            save_profile(profiles_dir, original)
            path = profile_path(profiles_dir, original.name)
            previous_contents = path.read_text(encoding="utf-8")

            updated = Profile("Équipe", ["Eni"], {}, now, now)
            with patch("dwm.storage.atomic.os.replace", side_effect=OSError("disk busy")):
                with self.assertRaises(OSError):
                    save_profile(profiles_dir, updated)

            self.assertEqual(path.read_text(encoding="utf-8"), previous_contents)
            self.assertEqual(list(profiles_dir.glob("*.tmp")), [])

    def test_corrupt_profile_does_not_replace_valid_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profiles_dir = Path(tmp)
            now = datetime.now().isoformat(timespec="seconds")
            profile = Profile("Équipe", ["Iop"], {}, now, now)
            save_profile(profiles_dir, profile)
            profile.order = ["Eni"]
            save_profile(profiles_dir, profile)

            path = profile_path(profiles_dir, profile.name)
            backup = profile_backup_path(path)
            valid_backup = backup.read_text(encoding="utf-8")
            path.write_text('{"schema_version":', encoding="utf-8")

            profile.order = ["Cra"]
            save_profile(profiles_dir, profile)

            self.assertEqual(backup.read_text(encoding="utf-8"), valid_backup)
            self.assertEqual(load_profile(profiles_dir, profile.name).order, ["Cra"])

    def test_future_profile_schema_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profiles_dir = Path(tmp)
            path = profile_path(profiles_dir, "Future")
            future = (
                '{"schema_version": '
                + str(PROFILE_SCHEMA_VERSION + 1)
                + ', "name": "Future"}'
            )
            path.write_text(future, encoding="utf-8")

            with self.assertRaises(ProfileSchemaTooNewError):
                load_profile(profiles_dir, "Future")

            now = datetime.now().isoformat(timespec="seconds")
            with self.assertRaises(ProfileSchemaTooNewError):
                save_profile(
                    profiles_dir,
                    Profile("Future", ["Iop"], {}, now, now),
                )

            self.assertEqual(path.read_text(encoding="utf-8"), future)

    def test_migrate_primitive_legacy_pickle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            formation_dir = root / "Formation"
            profiles_dir = root / "profiles"
            formation_dir.mkdir()
            with (formation_dir / "ancienne équipe.pkl").open("wb") as handle:
                pickle.dump({"order": ["Iop", "Eni"], "aliases": {"Iop": "Tank"}}, handle)

            migrated = migrate_pickles(formation_dir, profiles_dir)
            profile = load_profile(profiles_dir, "ancienne équipe")

        self.assertEqual(migrated, ["ancienne équipe"])
        self.assertEqual(profile.order, ["Iop", "Eni"])


if __name__ == "__main__":
    unittest.main()
