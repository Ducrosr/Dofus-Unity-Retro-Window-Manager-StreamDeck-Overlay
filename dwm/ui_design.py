from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UiMetrics:
    """Small, shared set of DWM layout metrics.

    The values intentionally stay conservative for a dense desktop interface:
    they standardise rhythm without turning DWM into a touch/mobile UI.
    """

    window_padding: int = 20
    compact_padding: int = 12
    section_gap: int = 16
    related_gap: int = 8
    work_area_margin: int = 24
    dialog_width: int = 500
    confirmation_width: int = 520
    main_content_max_width: int = 1600


UI = UiMetrics()

PRIMARY_BUTTON_STYLE = "Accent.TButton"
SECONDARY_BUTTON_STYLE = "Secondary.TButton"
TERTIARY_BUTTON_STYLE = "Tertiary.TButton"
DANGER_BUTTON_STYLE = "Danger.TButton"
