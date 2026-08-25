from __future__ import annotations

import unittest

from dwm.services.profile_matching import (
    rank_profile_matches,
    unique_exact_profile_match,
)
from dwm.storage.profiles import Profile


def profile(name: str, order: list[str], game_mode: str) -> Profile:
    return Profile(name, order, {}, "", "", game_mode=game_mode)


class ProfileMatchingTests(unittest.TestCase):
    def test_unique_exact_match_is_selected_case_insensitively(self) -> None:
        matches = rank_profile_matches(
            [
                profile("Jiva", ["Nealla", "Rubilax"], "unity"),
                profile("Boune", ["Nealla", "Rubilax"], "retro"),
            ],
            [" rubilax ", "NEALLA"],
            "unity",
        )

        self.assertEqual(unique_exact_profile_match(matches), "Jiva")
        self.assertTrue(matches[0].exact)

    def test_ambiguous_exact_match_never_chooses_a_profile(self) -> None:
        matches = rank_profile_matches(
            [
                profile("Serveur A", ["Iop", "Eni"], "unity"),
                profile("Serveur B", ["Iop", "Eni"], "unity"),
            ],
            ["Iop", "Eni"],
            "unity",
        )

        self.assertIsNone(unique_exact_profile_match(matches))
        self.assertEqual([match.name for match in matches], ["Serveur A", "Serveur B"])

    def test_partial_and_legacy_profiles_are_never_auto_selected(self) -> None:
        matches = rank_profile_matches(
            [
                profile("Partiel", ["Iop", "Eni", "Panda"], "unity"),
                profile("Ancien", ["Iop", "Eni"], ""),
            ],
            ["Iop", "Eni"],
            "unity",
        )

        self.assertEqual([match.name for match in matches], ["Partiel"])
        self.assertFalse(matches[0].exact)
        self.assertIsNone(unique_exact_profile_match(matches))

    def test_empty_detection_returns_no_matches(self) -> None:
        matches = rank_profile_matches(
            [profile("Jiva", ["Nealla"], "unity")],
            [],
            "unity",
        )
        self.assertEqual(matches, [])

