from __future__ import annotations

import tempfile
import unittest
import pickle
from datetime import datetime
from pathlib import Path

from dwm.storage.profiles import Profile, list_profiles, load_profile, migrate_pickles, profile_path, save_profile


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

    def test_list_profiles_is_case_insensitive_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profiles_dir = Path(tmp)
            for name in ("zeta", "Alpha"):
                now = datetime.now().isoformat(timespec="seconds")
                save_profile(profiles_dir, Profile(name, [], {}, now, now))
            names = list_profiles(profiles_dir)

        self.assertEqual(names, ["Alpha", "zeta"])

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
