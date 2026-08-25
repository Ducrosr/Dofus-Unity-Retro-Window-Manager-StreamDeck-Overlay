from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol, Sequence


class MatchableProfile(Protocol):
    name: str
    order: Sequence[str]
    game_mode: str


@dataclass(frozen=True)
class ProfileMatch:
    name: str
    overlap: int
    profile_size: int
    detected_size: int
    exact: bool


def normalize_character_name(value: object) -> str:
    return str(value or "").strip().casefold()


def rank_profile_matches(
    profiles: Iterable[MatchableProfile],
    detected_characters: Iterable[str],
    game_mode: str,
) -> list[ProfileMatch]:
    """Rank same-mode profiles without guessing across clients or servers.

    Legacy profiles without a recorded game mode are intentionally excluded:
    the application cannot safely classify them until the user loads and saves
    them once.
    """

    mode = str(game_mode or "").strip().lower()
    detected = {
        normalized
        for value in detected_characters
        if (normalized := normalize_character_name(value))
    }
    if not detected or mode not in {"unity", "retro"}:
        return []

    matches: list[ProfileMatch] = []
    for profile in profiles:
        if str(profile.game_mode or "").strip().lower() != mode:
            continue
        members = {
            normalized
            for value in profile.order
            if (normalized := normalize_character_name(value))
        }
        if not members:
            continue
        overlap = len(members & detected)
        if not overlap:
            continue
        matches.append(
            ProfileMatch(
                name=profile.name,
                overlap=overlap,
                profile_size=len(members),
                detected_size=len(detected),
                exact=members == detected,
            )
        )

    return sorted(
        matches,
        key=lambda match: (
            not match.exact,
            -match.overlap,
            abs(match.profile_size - match.detected_size),
            match.name.casefold(),
        ),
    )


def unique_exact_profile_match(matches: Iterable[ProfileMatch]) -> str | None:
    exact_names = [match.name for match in matches if match.exact]
    return exact_names[0] if len(exact_names) == 1 else None

