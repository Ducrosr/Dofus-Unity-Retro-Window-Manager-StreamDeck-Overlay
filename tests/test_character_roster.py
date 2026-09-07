from __future__ import annotations

import unittest

from dwm.models import GameWindow
from dwm.services.character_roster import CharacterRoster, character_names
from dwm.services.streamdeck_state import retain_character_slots
from dwm.storage.profiles import Profile
from dwm.storage.settings import Settings


def window(hwnd: int, name: str) -> GameWindow:
    return GameWindow(hwnd, f"{name} - Dofus", name, "")


class CharacterRosterTests(unittest.TestCase):
    def test_closed_client_keeps_slot_and_reconnects_with_new_handle(self):
        roster = CharacterRoster(order=["Panda", "Iop", "Eni"])
        windows = {1: window(1, "Panda"), 2: window(2, "Iop"), 3: window(3, "Eni")}
        roster.discover(windows)
        del windows[2]
        self.assertEqual(roster.bindings(windows), [1, -2, 3])
        windows[99] = window(99, "IOP")
        self.assertEqual(roster.bindings(windows), [1, 99, 3])
        self.assertEqual(roster.order, ["Panda", "Iop", "Eni"])

    def test_duplicate_names_never_choose_a_server(self):
        roster = CharacterRoster(slots=["Iop"])
        self.assertEqual(roster.bindings({1: window(1, "Iop"), 2: window(2, "iop")}), [-1])

    def test_reused_handle_does_not_retarget_a_character(self):
        roster = CharacterRoster(slots=["Iop", "Panda"])
        self.assertEqual(roster.bindings({1: window(1, "Panda")}), [-1, 1])

    def test_reordering_preserves_absent_and_ignored_positions_and_fixed_slots(self):
        roster = CharacterRoster(order=["A", "B", "C", "D"], slots=["A", "B", "C", "D"], ignored={"d"})
        roster.checkpoint()
        roster.remember_order({1: window(1, "A"), 3: window(3, "C"), 4: window(4, "D")}, [3, 1])
        self.assertEqual(roster.order, ["C", "B", "A", "D"])
        self.assertEqual(roster.slots, ["A", "B", "C", "D"])
        roster.discover({5: window(5, "E")})
        self.assertTrue(roster.undo())
        self.assertEqual(roster.order, ["A", "B", "C", "D", "E"])
        self.assertFalse(roster.undo())

    def test_undo_history_is_bounded(self):
        roster = CharacterRoster(order=["A"])
        for _ in range(30):
            roster.checkpoint()
        self.assertEqual(len(roster.history), 20)

    def test_profile_roundtrip_keeps_slots_and_ignored_names(self):
        profile = Profile("Serveur A", ["Panda", "Iop"], {}, "", "", game_mode="unity",
                          character_slots=["Iop", "Panda"], ignored_characters=["Panda"])
        restored = Profile.from_dict(profile.to_dict())
        self.assertEqual(restored.character_slots, ["Iop", "Panda"])
        self.assertEqual(restored.ignored_characters, ["Panda"])
        legacy = Profile.from_dict({"name": "Ancien", "order": ["Iop", "Panda"]})
        self.assertEqual(legacy.character_slots, ["Iop", "Panda"])
        self.assertEqual(legacy.ignored_characters, [])

    def test_invalid_names_are_not_treated_as_characters(self):
        self.assertEqual(character_names("Iop"), [])
        self.assertEqual(character_names([None, 8, " Iop ", "iop", "", "Panda"]), ["Iop", "Panda"])

    def test_settings_migration_preserves_global_positional_behavior(self):
        legacy = Settings.from_dict({"schema_version": 23})
        self.assertEqual(legacy.hotkey_scope, "global")
        self.assertFalse(legacy.fixed_character_slots)
        settings = Settings(hotkey_scope="game", fixed_character_slots=True)
        restored = Settings.from_dict(settings.to_dict())
        self.assertEqual(restored.hotkey_scope, "game")
        self.assertTrue(restored.fixed_character_slots)
        self.assertEqual(Settings(hotkey_scope="invalid").hotkey_scope, "global")

    def test_offline_streamdeck_entry_retains_name_and_never_shifts_next_slot(self):
        entries = [{"hwnd": 3, "slot": 2, "pseudo": "Eni"}, {"hwnd": 1, "slot": 1, "pseudo": "Panda"}]
        result = retain_character_slots(entries, ["Panda", "Iop", "Eni"], [1, -2, 3], {"Iop": "Terre"}, {})
        self.assertEqual([entry["hwnd"] for entry in result], [1, -2, 3])
        self.assertEqual(result[1]["name"], "Iop")
        self.assertFalse(result[1]["available"])
        self.assertEqual(result[1]["alias"], "Terre")
        self.assertEqual(result[2]["slot"], 3)
