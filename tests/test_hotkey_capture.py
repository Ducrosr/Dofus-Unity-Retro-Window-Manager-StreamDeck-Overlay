from __future__ import annotations

import unittest

from dwm.services.hotkey_capture import (
    captured_hotkey_spec,
    describe_registration_errors,
    find_hotkey_conflicts,
)


class HotkeyCaptureTests(unittest.TestCase):
    def test_capture_formats_modifiers_and_supported_keys(self) -> None:
        self.assertEqual(captured_hotkey_spec("F8", 0x0004 | 0x0001), "Ctrl+Shift+F8")
        self.assertEqual(captured_hotkey_spec("a", 0x0008), "Alt+A")
        self.assertEqual(captured_hotkey_spec("Return", 0x0040), "Win+Enter")

    def test_modifier_only_or_unsupported_key_keeps_capture_open(self) -> None:
        self.assertIsNone(captured_hotkey_spec("Control_L", 0x0004))
        self.assertIsNone(captured_hotkey_spec("dead_circumflex", 0))

    def test_duplicate_detection_uses_the_parsed_hotkey_identity(self) -> None:
        def parser(spec: str) -> tuple[str, ...]:
            return tuple(sorted(part.casefold() for part in spec.split("+")))

        conflicts = find_hotkey_conflicts(
            [
                ("Suivant", "Ctrl+F5"),
                ("Fenêtre 1", "F5+CTRL"),
                ("Précédent", "F6"),
                ("Vide", ""),
            ],
            parser,
        )
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].labels, ("Suivant", "Fenêtre 1"))

    def test_windows_registration_errors_are_labeled(self) -> None:
        description = describe_registration_errors(
            ["RegisterHotKey a échoué (id=5, vk=119, mods=0)"],
            {5: "Prochaine fenêtre en attente"},
        )
        self.assertIn("Prochaine fenêtre en attente", description)
        self.assertIn("déjà utilisée", description)

