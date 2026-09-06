from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..storage.profiles import Profile, profile_path


@dataclass(frozen=True)
class ConfigurationChange:
    section: str
    path: tuple[str, ...]
    before: object
    after: object


def compare_values(before: object, after: object, *, section: str,
                   path: tuple[str, ...] = ()) -> list[ConfigurationChange]:
    if before == after:
        return []
    if isinstance(before, dict) and isinstance(after, dict):
        changes = []
        for key in sorted(before.keys() | after.keys()):
            changes.extend(compare_values(before.get(key), after.get(key),
                                          section=section, path=(*path, str(key))))
        return changes
    return [ConfigurationChange(section, path, before, after)]


def profile_identity(profile: Profile) -> str:
    # Match the filename actually replaced on Windows, including sanitized names.
    return profile_path(Path("."), profile.name).name.casefold()


def compare_profiles(current: list[Profile], incoming: list[Profile]) -> tuple[list[ConfigurationChange], int]:
    existing = {profile_identity(profile): profile for profile in current}
    targets = [profile_identity(profile) for profile in incoming]
    if len(set(targets)) != len(targets):
        raise ValueError("Plusieurs profils importés utilisent le même nom de fichier.")
    changes = []
    for profile in incoming:
        old = existing.get(profile_identity(profile))
        def content(value):
            if value is None:
                return None
            return {key: item for key, item in value.to_dict().items()
                    if key not in {"created_at", "updated_at", "schema_version"}}
        changes.extend(compare_values(content(old), content(profile), section="Profils", path=(profile.name,)))
    return changes, len(set(existing) - set(targets))


def compare_configuration(current_settings: dict, incoming_settings: dict,
                          current_profiles: list[Profile], incoming_profiles: list[Profile],
                          current_session: dict, incoming_session: dict) -> tuple[list[ConfigurationChange], int]:
    changes = compare_values(
        {key: value for key, value in current_settings.items() if key != "schema_version"},
        {key: value for key, value in incoming_settings.items() if key != "schema_version"},
        section="Paramètres",
    )
    profile_changes, retained = compare_profiles(current_profiles, incoming_profiles)
    changes.extend(profile_changes)
    changes.extend(compare_values(current_session, incoming_session, section="Session actuelle"))
    return changes, retained
