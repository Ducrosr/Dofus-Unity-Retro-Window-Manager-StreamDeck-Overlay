from __future__ import annotations

from dataclasses import dataclass

from .display_overlay import clamp_overlay_opacity, normalize_overlay_orientation
from .game_mode import normalize_game_mode
from .i18n import normalize_language


@dataclass(frozen=True)
class OnboardingChoices:
    language: str
    game_mode: str
    event_hook_enabled: bool
    auto_refresh: bool
    overlay_enabled: bool
    overlay_orientation: str
    overlay_opacity: int
    overlay_show_title: bool
    overlay_show_reorder_buttons: bool


def onboarding_required(settings) -> bool:
    """Return whether the guided setup still needs to be completed."""
    return not bool(getattr(settings, "onboarding_completed", False))


def apply_onboarding_choices(settings, choices: OnboardingChoices) -> None:
    """Normalize and persist the guided setup choices on a Settings object."""
    mode = normalize_game_mode(choices.game_mode, getattr(settings, "game_mode", "unity"))
    settings.language = normalize_language(choices.language)
    settings.game_mode = mode
    settings.activate_display_preferences(mode)
    settings.event_hook_enabled = bool(choices.event_hook_enabled)
    settings.auto_refresh = bool(choices.auto_refresh)
    settings.rotation_overlay_enabled = bool(choices.overlay_enabled)
    settings.rotation_overlay_orientation = normalize_overlay_orientation(
        choices.overlay_orientation
    )
    settings.rotation_overlay_opacity = clamp_overlay_opacity(
        choices.overlay_opacity
    )
    settings.rotation_overlay_show_title = bool(choices.overlay_show_title)
    settings.rotation_overlay_show_reorder_buttons = bool(
        choices.overlay_show_reorder_buttons
    )
    settings.remember_display_preferences(mode)
    settings.onboarding_completed = True
