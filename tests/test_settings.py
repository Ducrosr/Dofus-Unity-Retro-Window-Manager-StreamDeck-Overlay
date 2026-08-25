from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dwm.storage.atomic import atomic_write_text
from dwm.storage.settings import (
    DEFAULT_WINDOW_COLUMN_ORDER,
    MODERN_DARK_THEME,
    Settings,
    load_settings,
    save_settings,
    settings_backup_path,
)
from dwm.services.display_overlay import DEFAULT_ROTATION_OVERLAY_LAYOUT
from dwm.services.themes import RETRO_THEME, UNITY_STANDARD_THEME


class SettingsTests(unittest.TestCase):
    def test_defaults_are_complete(self) -> None:
        settings = Settings()
        self.assertEqual(settings.game_mode, "unity")
        self.assertFalse(settings.security_notice_accepted)
        self.assertFalse(settings.onboarding_completed)
        self.assertEqual(settings.hotkeys["forward"], "F5")
        self.assertEqual(settings.hotkeys["next_attention"], "F8")
        self.assertEqual(settings.hotkeys["refresh"], "Ctrl+Alt+R")
        self.assertEqual(settings.window_column_order, list(DEFAULT_WINDOW_COLUMN_ORDER))
        self.assertEqual(settings.theme, MODERN_DARK_THEME)
        self.assertTrue(settings.minimize_to_tray)
        self.assertFalse(settings.start_with_windows)
        self.assertTrue(settings.check_updates_automatically)
        self.assertTrue(settings.include_prereleases)
        self.assertEqual(settings.last_update_check_at, "")
        self.assertTrue(settings.swap_notification_enabled)
        self.assertEqual(settings.swap_notification_anchor, "top_center")
        self.assertEqual(settings.swap_notification_duration_ms, 1400)
        self.assertEqual(settings.swap_notification_opacity, 88)
        self.assertTrue(settings.rotation_overlay_enabled)
        self.assertEqual(settings.rotation_overlay_opacity, 88)
        self.assertFalse(settings.rotation_overlay_locked)
        self.assertEqual(settings.rotation_overlay_layout, DEFAULT_ROTATION_OVERLAY_LAYOUT)
        self.assertEqual(settings.swap_notification_layout, DEFAULT_ROTATION_OVERLAY_LAYOUT)
        self.assertEqual((settings.rotation_overlay_width, settings.rotation_overlay_height), (300, 0))
        self.assertTrue(settings.rotation_overlay_auto_width)
        self.assertEqual(settings.rotation_overlay_orientation, "vertical")
        self.assertTrue(settings.rotation_overlay_show_title)
        self.assertTrue(settings.rotation_overlay_show_reorder_buttons)
        self.assertTrue(settings.attention_blink_enabled)
        self.assertTrue(settings.show_popup_portraits)
        self.assertTrue(settings.show_popup_badges)
        self.assertTrue(settings.show_overlay_portraits)
        self.assertTrue(settings.show_overlay_badges)
        self.assertTrue(settings.show_character_portraits)
        self.assertTrue(settings.show_character_badges)
        self.assertEqual(settings.character_visuals, {})
        self.assertTrue(settings.smart_profile_loading_enabled)
        self.assertTrue(settings.adaptive_performance_enabled)
        self.assertFalse(settings.accessibility_high_contrast)
        self.assertFalse(settings.accessibility_reduce_motion)
        self.assertEqual(settings.accessibility_ui_scale_percent, 100)
        self.assertTrue(all(settings.hotkeys[f"window_{position}"] == "" for position in range(1, 9)))

    def test_column_order_is_sanitized_and_completed(self) -> None:
        settings = Settings(window_column_order=["alias", "invalid", "class", "alias"])

        self.assertEqual(settings.window_column_order, ["alias", "class", "name", "hwnd"])

    def test_old_retro_filter_is_migrated(self) -> None:
        settings = Settings.from_dict(
            {
                "schema_version": 2,
                "retro_title_keyword": "dofus",
                "retro_process_keyword": "dofus",
            }
        )
        self.assertEqual(settings.retro_title_keyword, "dofus retro v")
        self.assertEqual(settings.retro_process_keyword, "")

    def test_historical_default_theme_is_migrated(self) -> None:
        settings = Settings.from_dict({"schema_version": 7, "theme": "equilux"})

        self.assertEqual(settings.theme, MODERN_DARK_THEME)

    def test_existing_installation_does_not_reopen_the_new_onboarding(self) -> None:
        settings = Settings.from_dict(
            {
                "schema_version": 19,
                "security_notice_accepted": True,
            }
        )

        self.assertTrue(settings.onboarding_completed)

    def test_removed_external_theme_is_migrated_to_standard(self) -> None:
        settings = Settings.from_dict({"schema_version": 7, "theme": "arc"})

        self.assertEqual(settings.theme, UNITY_STANDARD_THEME)

    def test_save_then_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            expected = Settings(
                game_mode="retro",
                language="es",
                security_notice_accepted=True,
                onboarding_completed=True,
                refresh_seconds=7,
                adaptive_performance_enabled=False,
                accessibility_high_contrast=True,
                accessibility_reduce_motion=True,
                accessibility_ui_scale_percent=125,
                last_profile="Équipe",
                window_column_order=["name", "alias", "class", "hwnd"],
                check_updates_automatically=False,
                include_prereleases=False,
                last_update_check_at="2026-08-22T12:00:00Z",
                compact_window_geometry="340x260+20+40",
                swap_notification_enabled=False,
                swap_notification_anchor="bottom_right",
                swap_notification_duration_ms=2200,
                swap_notification_opacity=71,
                swap_notification_layout={
                    "left": "class",
                    "line1": "name",
                    "line2_left": "alias",
                    "line2_right": "none",
                },
                rotation_overlay_enabled=True,
                rotation_overlay_x=-250,
                rotation_overlay_y=90,
                rotation_overlay_opacity=72,
                rotation_overlay_locked=True,
                rotation_overlay_width=440,
                rotation_overlay_auto_width=False,
                rotation_overlay_height=520,
                rotation_overlay_show_title=False,
                rotation_overlay_show_reorder_buttons=False,
                attention_blink_enabled=False,
                show_popup_portraits=False,
                show_popup_badges=False,
                show_overlay_portraits=True,
                show_overlay_badges=True,
                show_character_portraits=False,
                show_character_badges=False,
                character_visuals={"Nealla": {"portrait": "", "badge": "ankama_force"}},
                rotation_overlay_layout={
                    "left": "class",
                    "line1": "alias",
                    "line2_left": "name",
                    "line2_right": "none",
                },
            )
            save_settings(path, expected)
            actual = load_settings(path)

        self.assertEqual(actual.game_mode, "retro")
        self.assertEqual(actual.language, "es")
        self.assertTrue(actual.security_notice_accepted)
        self.assertTrue(actual.onboarding_completed)
        self.assertEqual(actual.refresh_seconds, 7)
        self.assertFalse(actual.adaptive_performance_enabled)
        self.assertTrue(actual.accessibility_high_contrast)
        self.assertTrue(actual.accessibility_reduce_motion)
        self.assertEqual(actual.accessibility_ui_scale_percent, 125)
        self.assertEqual(actual.last_profile, "Équipe")
        self.assertTrue(actual.smart_profile_loading_enabled)
        self.assertEqual(actual.window_column_order, ["name", "alias", "class", "hwnd"])
        self.assertFalse(actual.check_updates_automatically)
        self.assertFalse(actual.include_prereleases)
        self.assertEqual(actual.last_update_check_at, "2026-08-22T12:00:00Z")
        self.assertEqual(actual.compact_window_geometry, "340x260+20+40")
        self.assertFalse(actual.swap_notification_enabled)
        self.assertEqual(actual.swap_notification_anchor, "bottom_right")
        self.assertEqual(actual.swap_notification_duration_ms, 2200)
        self.assertEqual(actual.swap_notification_opacity, 71)
        self.assertEqual(
            actual.swap_notification_layout,
            {
                "left": "class",
                "line1": "name",
                "line2_left": "alias",
                "line2_right": "none",
            },
        )
        self.assertTrue(actual.rotation_overlay_enabled)
        self.assertEqual((actual.rotation_overlay_x, actual.rotation_overlay_y), (-250, 90))
        self.assertEqual(actual.rotation_overlay_opacity, 72)
        self.assertTrue(actual.rotation_overlay_locked)
        self.assertEqual((actual.rotation_overlay_width, actual.rotation_overlay_height), (440, 520))
        self.assertFalse(actual.rotation_overlay_auto_width)
        self.assertFalse(actual.rotation_overlay_show_title)
        self.assertFalse(actual.rotation_overlay_show_reorder_buttons)
        self.assertFalse(actual.attention_blink_enabled)
        self.assertFalse(actual.show_popup_portraits)
        self.assertFalse(actual.show_popup_badges)
        self.assertTrue(actual.show_overlay_portraits)
        self.assertTrue(actual.show_overlay_badges)
        self.assertFalse(actual.show_character_portraits)
        self.assertFalse(actual.show_character_badges)
        self.assertEqual(actual.character_visuals, {"Nealla": {"portrait": "", "badge": "ankama_force"}})
        self.assertEqual(
            actual.rotation_overlay_layout,
            {
                "left": "class",
                "line1": "alias",
                "line2_left": "name",
                "line2_right": "none",
            },
        )

    def test_corrupt_settings_fall_back_to_last_valid_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            save_settings(path, Settings(language="en", refresh_seconds=6))
            save_settings(path, Settings(language="es", refresh_seconds=12))

            backup = settings_backup_path(path)
            self.assertTrue(backup.exists())
            path.write_text('{"schema_version":', encoding="utf-8")
            recovered = load_settings(path)

        self.assertEqual(recovered.language, "en")
        self.assertEqual(recovered.refresh_seconds, 6)

    def test_atomic_write_failure_preserves_original_and_cleans_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            path.write_text("original", encoding="utf-8")

            with patch("dwm.storage.atomic.os.replace", side_effect=OSError("disk busy")):
                with self.assertRaises(OSError):
                    atomic_write_text(path, "replacement")

            self.assertEqual(path.read_text(encoding="utf-8"), "original")
            self.assertEqual(list(Path(tmp).glob("*.tmp")), [])

    def test_overlay_values_are_clamped(self) -> None:
        settings = Settings(
            swap_notification_anchor="somewhere",
            swap_notification_duration_ms=50,
            swap_notification_opacity=2,
            rotation_overlay_opacity=200,
            rotation_overlay_width=5,
            rotation_overlay_height=9999,
        )

        self.assertEqual(settings.swap_notification_anchor, "top_center")
        self.assertEqual(settings.swap_notification_duration_ms, 600)
        self.assertEqual(settings.swap_notification_opacity, 35)
        self.assertEqual(settings.rotation_overlay_opacity, 100)
        self.assertEqual((settings.rotation_overlay_width, settings.rotation_overlay_height), (80, 1600))

    def test_themes_are_remembered_per_game_mode(self) -> None:
        settings = Settings(
            game_mode="retro",
            theme="dwm-dark",
            theme_by_game_mode={"unity": "unity-bonta", "retro": RETRO_THEME},
        )

        self.assertEqual(settings.theme, RETRO_THEME)
        self.assertEqual(settings.theme_by_game_mode["unity"], "unity-bonta")
        self.assertEqual(settings.theme_by_game_mode["retro"], RETRO_THEME)

    def test_retro_uses_standard_theme_by_default(self) -> None:
        settings = Settings(game_mode="retro")

        self.assertEqual(settings.theme, UNITY_STANDARD_THEME)

    def test_invalid_theme_and_language_use_safe_defaults(self) -> None:
        settings = Settings(game_mode="unity", theme="arc", language="de")

        self.assertEqual(settings.theme, UNITY_STANDARD_THEME)
        self.assertEqual(settings.language, "fr")

    def test_previous_schema_receives_safe_display_defaults(self) -> None:
        settings = Settings.from_dict({"schema_version": 10, "theme": MODERN_DARK_THEME})

        self.assertFalse(settings.security_notice_accepted)
        self.assertTrue(settings.swap_notification_enabled)
        self.assertFalse(settings.rotation_overlay_enabled)
        self.assertEqual(settings.swap_notification_opacity, 96)
        self.assertFalse(settings.rotation_overlay_locked)
        self.assertEqual(settings.rotation_overlay_layout, DEFAULT_ROTATION_OVERLAY_LAYOUT)
        self.assertTrue(settings.rotation_overlay_show_title)
        self.assertTrue(settings.rotation_overlay_show_reorder_buttons)

    def test_legacy_portrait_preference_migrates_to_each_display(self) -> None:
        settings = Settings.from_dict({"schema_version": 14, "show_character_portraits": False})

        self.assertFalse(settings.show_popup_portraits)
        self.assertFalse(settings.show_overlay_portraits)
        self.assertFalse(settings.show_character_portraits)

    def test_legacy_badge_preference_migrates_to_each_display(self) -> None:
        settings = Settings.from_dict({"schema_version": 15, "show_character_badges": False})

        self.assertFalse(settings.show_popup_badges)
        self.assertFalse(settings.show_overlay_badges)
        self.assertFalse(settings.show_character_badges)

    def test_legacy_custom_overlay_width_remains_manual(self) -> None:
        settings = Settings.from_dict(
            {"schema_version": 15, "rotation_overlay_width": 460}
        )

        self.assertEqual(settings.rotation_overlay_width, 460)
        self.assertFalse(settings.rotation_overlay_auto_width)

    def test_display_reset_preserves_user_data_and_restores_safe_geometry(self) -> None:
        settings = Settings(
            game_mode="unity",
            language="es",
            hotkeys={"forward": "F8"},
            theme="unity-brakmar",
            window_column_order=["name", "alias", "class", "hwnd"],
            rotation_overlay_enabled=True,
            rotation_overlay_x=9000,
            rotation_overlay_y=-8000,
            rotation_overlay_width=880,
            rotation_overlay_height=1400,
            attention_blink_enabled=False,
            show_popup_portraits=False,
            character_visuals={"Nealla": {"portrait": "", "badge": "ankama_force"}},
        )

        settings.reset_display_preferences("unity")

        self.assertEqual(settings.language, "es")
        self.assertEqual(settings.hotkeys["forward"], "F8")
        self.assertEqual(settings.character_visuals, {"Nealla": {"portrait": "", "badge": "ankama_force"}})
        self.assertEqual(settings.theme, UNITY_STANDARD_THEME)
        self.assertEqual(settings.window_column_order, list(DEFAULT_WINDOW_COLUMN_ORDER))
        self.assertTrue(settings.rotation_overlay_enabled)
        self.assertEqual((settings.rotation_overlay_x, settings.rotation_overlay_y), (24, 160))
        self.assertEqual((settings.rotation_overlay_width, settings.rotation_overlay_height), (300, 0))
        self.assertTrue(settings.rotation_overlay_auto_width)
        self.assertTrue(settings.rotation_overlay_show_title)
        self.assertTrue(settings.rotation_overlay_show_reorder_buttons)
        self.assertTrue(settings.attention_blink_enabled)
        self.assertTrue(settings.show_popup_portraits)
        self.assertTrue(settings.show_popup_badges)
        self.assertTrue(settings.show_overlay_portraits)
        self.assertTrue(settings.show_overlay_badges)

    def test_display_preferences_are_independent_per_game_mode(self) -> None:
        settings = Settings(game_mode="unity")
        settings.rotation_overlay_enabled = False
        settings.swap_notification_opacity = 61
        settings.rotation_overlay_orientation = "horizontal"
        settings.rotation_overlay_show_title = False
        settings.rotation_overlay_show_reorder_buttons = False
        settings.remember_display_preferences("unity")

        settings.game_mode = "retro"
        settings.activate_display_preferences("retro")
        self.assertTrue(settings.rotation_overlay_enabled)
        self.assertEqual(settings.swap_notification_opacity, 88)
        self.assertEqual(settings.rotation_overlay_orientation, "vertical")
        self.assertTrue(settings.rotation_overlay_show_title)
        self.assertTrue(settings.rotation_overlay_show_reorder_buttons)

        settings.rotation_overlay_opacity = 54
        settings.remember_display_preferences("retro")
        settings.game_mode = "unity"
        settings.activate_display_preferences("unity")

        self.assertFalse(settings.rotation_overlay_enabled)
        self.assertEqual(settings.swap_notification_opacity, 61)
        self.assertEqual(settings.rotation_overlay_orientation, "horizontal")
        self.assertFalse(settings.rotation_overlay_show_title)
        self.assertFalse(settings.rotation_overlay_show_reorder_buttons)

        restored = Settings.from_dict(settings.to_dict())
        self.assertEqual(
            restored.display_by_game_mode["retro"]["rotation_overlay_opacity"],
            54,
        )


if __name__ == "__main__":
    unittest.main()
