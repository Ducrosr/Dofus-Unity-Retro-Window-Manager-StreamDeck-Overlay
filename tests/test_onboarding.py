from __future__ import annotations

import unittest

from dwm.services.onboarding import (
    OnboardingChoices,
    apply_onboarding_choices,
    onboarding_required,
)
from dwm.storage.settings import Settings
from main import should_prompt_for_game_mode


class OnboardingTests(unittest.TestCase):
    def test_new_install_requires_onboarding(self) -> None:
        settings = Settings()

        self.assertTrue(onboarding_required(settings))
        self.assertFalse(
            should_prompt_for_game_mode(settings, use_saved_mode=False)
        )

    def test_completed_install_keeps_the_regular_mode_picker(self) -> None:
        settings = Settings(onboarding_completed=True)

        self.assertTrue(should_prompt_for_game_mode(settings, use_saved_mode=False))
        self.assertFalse(should_prompt_for_game_mode(settings, use_saved_mode=True))

    def test_choices_are_normalized_and_saved_for_the_selected_game_mode(self) -> None:
        settings = Settings(game_mode="unity")

        apply_onboarding_choices(
            settings,
            OnboardingChoices(
                language="ES-es",
                game_mode="retro",
                event_hook_enabled=False,
                auto_refresh=False,
                overlay_enabled=True,
                overlay_orientation="horizontal",
                overlay_opacity=140,
                overlay_show_title=False,
                overlay_show_reorder_buttons=False,
            ),
        )

        self.assertFalse(onboarding_required(settings))
        self.assertEqual(settings.language, "es")
        self.assertEqual(settings.game_mode, "retro")
        self.assertFalse(settings.event_hook_enabled)
        self.assertFalse(settings.auto_refresh)
        self.assertTrue(settings.rotation_overlay_enabled)
        self.assertEqual(settings.rotation_overlay_orientation, "horizontal")
        self.assertEqual(settings.rotation_overlay_opacity, 100)
        self.assertFalse(settings.rotation_overlay_show_title)
        self.assertFalse(settings.rotation_overlay_show_reorder_buttons)
        self.assertEqual(
            settings.display_by_game_mode["retro"]["rotation_overlay_orientation"],
            "horizontal",
        )
        self.assertEqual(
            settings.display_by_game_mode["unity"]["rotation_overlay_orientation"],
            "vertical",
        )


if __name__ == "__main__":
    unittest.main()
