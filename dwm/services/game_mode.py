from __future__ import annotations


GAME_MODES = ("unity", "retro")


def normalize_game_mode(game_mode: str | None, fallback: str = "unity") -> str:
    mode = str(game_mode or "").strip().lower()
    if mode in GAME_MODES:
        return mode
    fallback_mode = str(fallback or "unity").strip().lower()
    return fallback_mode if fallback_mode in GAME_MODES else "unity"


def game_mode_label(game_mode: str | None) -> str:
    return "Retro" if normalize_game_mode(game_mode) == "retro" else "Unity"


def win_event_filter(
    game_mode: str | None,
    retro_title_keyword: str | None,
) -> tuple[tuple[str, ...], dict[str, str] | None]:
    mode = normalize_game_mode(game_mode)
    if mode == "unity":
        return ("UnityWndClass",), None
    keyword = str(retro_title_keyword or "dofus retro v").strip().lower() or "dofus retro v"
    return ("Chrome_WidgetWin_1",), {"Chrome_WidgetWin_1": keyword}
