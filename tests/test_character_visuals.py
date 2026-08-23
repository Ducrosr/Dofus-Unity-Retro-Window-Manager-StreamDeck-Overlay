from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from dwm.services.character_visuals import (
    badge_from_label,
    badge_label,
    bundled_icon_data_uri,
    bundled_portrait_choices,
    build_avatar_image,
    build_badge_tile_image,
    decode_portrait_data,
    encode_portrait_file,
    normalize_badge,
    sanitize_character_visuals,
)


class CharacterVisualsTests(unittest.TestCase):
    def test_portrait_is_converted_to_a_small_png_data_uri(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "portrait.jpg"
            Image.new("RGB", (320, 180), "#ef4444").save(path, format="JPEG")

            data = encode_portrait_file(path)
            decoded = decode_portrait_data(data)

        self.assertTrue(data.startswith("data:image/png;base64,"))
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded.size, (96, 96))

    def test_visual_settings_reject_invalid_data_and_badges(self) -> None:
        visuals = sanitize_character_visuals(
            {
                "Nealla": {"portrait": "data:image/png;base64,invalid", "badge": "ankama_force"},
                "Nat": {"portrait": "", "badge": "unknown"},
                "": {"portrait": "", "badge": "earth"},
            }
        )

        self.assertEqual(visuals, {"Nealla": {"portrait": "", "badge": "ankama_force"}})
        self.assertEqual(normalize_badge("UNKNOWN"), "none")
        self.assertEqual(normalize_badge("earth"), "none")
        self.assertEqual(badge_from_label(badge_label("ankama_force")), "ankama_force")

    def test_avatar_falls_back_to_initial_and_draws_a_badge(self) -> None:
        avatar = build_avatar_image("Nealla", badge="ankama_force", size=64)

        self.assertEqual(avatar.size, (64, 64))
        self.assertEqual(avatar.mode, "RGBA")

    def test_standalone_badge_does_not_require_a_character_portrait(self) -> None:
        characteristic = build_badge_tile_image("ankama_force", size=64)
        profession = build_badge_tile_image("ankama_metier_mineur", size=64)

        self.assertEqual(characteristic.size, (64, 64))
        self.assertEqual(profession.size, (64, 64))
        self.assertIsNotNone(characteristic.getbbox())
        self.assertIsNotNone(profession.getbbox())

    def test_bundled_ankama_assets_are_available(self) -> None:
        portraits = bundled_portrait_choices()
        icon_data = bundled_icon_data_uri("ankama_force")
        profession_data = bundled_icon_data_uri("ankama_metier_alchimiste")
        avatar = build_avatar_image("Nealla", badge="ankama_force", size=64)

        self.assertEqual(len(portraits), 38)
        self.assertIn("Pandawa — Féminin", portraits)
        self.assertTrue(icon_data.startswith("data:image/png;base64,"))
        self.assertTrue(profession_data.startswith("data:image/png;base64,"))
        self.assertEqual(avatar.size, (64, 64))


if __name__ == "__main__":
    unittest.main()
