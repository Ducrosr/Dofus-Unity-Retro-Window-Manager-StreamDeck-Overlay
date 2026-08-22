from __future__ import annotations

import unittest
from unittest.mock import patch

from dwm.services import windows
from dwm.services.windows import extract_character_class, extract_pseudo, extract_pseudo_retro, extract_pseudo_unity


class WindowTitleTests(unittest.TestCase):
    def test_extract_unity_pseudo(self) -> None:
        self.assertEqual(extract_pseudo("Craette - Dofus"), "Craette")
        self.assertEqual(extract_pseudo("  Iopette serveur  "), "Iopette")
        self.assertEqual(extract_pseudo(""), "")

    def test_extract_unity_pseudo_supports_name_then_class(self) -> None:
        self.assertEqual(extract_pseudo_unity("Korra - Féca - 3.4.1.17"), "Korra")
        self.assertEqual(extract_pseudo_unity("Dofus — Korra — Féca — 3.4.1.17"), "Korra")

    def test_extract_unity_pseudo_supports_class_then_name(self) -> None:
        self.assertEqual(extract_pseudo_unity("Féca - Korra - 3.4.1.17"), "Korra")
        self.assertEqual(extract_pseudo_unity("Dofus | Féca | Korra | Release"), "Korra")

    def test_extract_unity_character_class(self) -> None:
        self.assertEqual(extract_character_class("Korra - Féca - Dofus", "Korra"), "Féca")
        self.assertEqual(extract_character_class("Craette | CRA | Dofus", "Craette"), "Crâ")
        self.assertEqual(extract_character_class("Dofus - Nox - Huppermage", "Nox"), "Huppermage")

    def test_character_class_does_not_confuse_leading_pseudo(self) -> None:
        self.assertEqual(extract_character_class("Iop - Dofus", "Iop"), "")
        self.assertEqual(extract_character_class("Iop - Iop - Dofus", "Iop"), "Iop")

    def test_unity_scanner_keeps_character_class(self) -> None:
        with patch.object(
            windows,
            "enum_top_level_windows",
            return_value=[(101, "Korra - Féca - Dofus")],
        ):
            result = windows.list_unity_windows()

        self.assertEqual(result[0].pseudo, "Korra")
        self.assertEqual(result[0].character_class, "Féca")

    def test_unity_scanner_separates_class_first_title(self) -> None:
        with patch.object(
            windows,
            "enum_top_level_windows",
            return_value=[(101, "Féca - Korra - 3.4.1.17")],
        ):
            result = windows.list_unity_windows()

        self.assertEqual(result[0].pseudo, "Korra")
        self.assertEqual(result[0].character_class, "Féca")

    def test_extract_retro_pseudo_before_marker(self) -> None:
        self.assertEqual(extract_pseudo_retro("Eniripsa - Dofus Retro v1.44"), "Eniripsa")

    def test_extract_retro_pseudo_after_marker(self) -> None:
        self.assertEqual(extract_pseudo_retro("Dofus Retro v1.44 - Sacrieur"), "Sacrieur")

    def test_extract_retro_pseudo_with_server_suffix(self) -> None:
        self.assertEqual(extract_pseudo_retro("Xelor - Dofus Retro v1.44 - Boune"), "Xelor")

    def test_visible_dofus_candidates_report_unknown_class(self) -> None:
        visible = [
            (10, "Dofus 3.1.2.1 - Release"),
            (11, "Dofus Window Manager 2.13.1"),
            (12, "Navigateur"),
        ]
        with (
            patch.object(windows, "enum_top_level_windows", return_value=visible),
            patch.object(windows, "get_class_name", return_value="NouvelleClasseUnity"),
        ):
            candidates = windows.list_visible_dofus_candidates()

        self.assertEqual(candidates, [(10, "Dofus 3.1.2.1 - Release", "NouvelleClasseUnity")])


if __name__ == "__main__":
    unittest.main()
