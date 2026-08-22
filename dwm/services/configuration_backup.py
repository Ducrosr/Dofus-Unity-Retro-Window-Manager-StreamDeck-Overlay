from __future__ import annotations

from datetime import datetime
from typing import Any

from ..storage.profiles import Profile
from ..storage.settings import Settings


BACKUP_FORMAT = "dofus-window-manager-backup"
BACKUP_SCHEMA_VERSION = 1


def build_configuration_backup(
    settings: Settings,
    profiles: list[Profile],
    *,
    active_profile: str,
    current_order: list[str],
    current_aliases: dict[str, str],
    app_version: str,
) -> dict[str, Any]:
    aliases = {pseudo: alias.strip() for pseudo, alias in current_aliases.items() if alias.strip()}
    return {
        "format": BACKUP_FORMAT,
        "schema_version": BACKUP_SCHEMA_VERSION,
        "app_version": app_version,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "settings": settings.to_dict(),
        "profiles": [profile.to_dict() for profile in profiles],
        "current_session": {
            "active_profile": active_profile.strip(),
            "order": list(current_order),
            "aliases": aliases,
        },
    }


def parse_configuration_backup(data: object) -> tuple[Settings, list[Profile], dict[str, object]]:
    if not isinstance(data, dict) or data.get("format") != BACKUP_FORMAT:
        raise ValueError("Ce fichier n’est pas une sauvegarde Dofus Window Manager.")
    schema = int(data.get("schema_version", 0) or 0)
    if schema != BACKUP_SCHEMA_VERSION:
        raise ValueError(f"Version de sauvegarde non prise en charge : {schema}.")

    raw_settings = data.get("settings")
    if not isinstance(raw_settings, dict):
        raise ValueError("La sauvegarde ne contient pas de paramètres valides.")
    settings = Settings.from_dict(raw_settings)

    profiles: list[Profile] = []
    raw_profiles = data.get("profiles")
    if not isinstance(raw_profiles, list):
        raise ValueError("La liste des profils est invalide.")
    for raw_profile in raw_profiles:
        if not isinstance(raw_profile, dict):
            raise ValueError("Un profil de la sauvegarde est invalide.")
        profile = Profile.from_dict(raw_profile)
        if not profile.name.strip():
            raise ValueError("Un profil de la sauvegarde n’a pas de nom.")
        profiles.append(profile)

    raw_session = data.get("current_session")
    session = raw_session if isinstance(raw_session, dict) else {}
    order = [str(value) for value in (session.get("order") or []) if str(value).strip()]
    raw_aliases = session.get("aliases") or {}
    aliases = (
        {str(pseudo): str(alias).strip() for pseudo, alias in raw_aliases.items() if str(alias).strip()}
        if isinstance(raw_aliases, dict)
        else {}
    )
    normalized_session: dict[str, object] = {
        "active_profile": str(session.get("active_profile") or "").strip(),
        "order": order,
        "aliases": aliases,
    }
    return settings, profiles, normalized_session
