from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class StreamDeckPluginHealth:
    status: str
    installed_version: str | None
    bundled_version: str | None
    repair_recommended: bool
    message: str


def _version_parts(value: str | None) -> tuple[int, ...] | None:
    if not value or not re.fullmatch(r"\d+(?:\.\d+)*", value.strip()):
        return None
    return tuple(int(part) for part in value.split("."))


def evaluate_streamdeck_plugin_health(
    installed_version: str | None,
    bundled_version: str | None,
) -> StreamDeckPluginHealth:
    installed = _version_parts(installed_version)
    bundled = _version_parts(bundled_version)
    if bundled is None:
        return StreamDeckPluginHealth(
            "bundled_missing",
            installed_version,
            bundled_version,
            False,
            "Le paquet Stream Deck fourni avec l’application est introuvable ou invalide.",
        )
    if installed is None:
        return StreamDeckPluginHealth(
            "missing",
            installed_version,
            bundled_version,
            True,
            f"Plugin non détecté. La version {bundled_version} peut être installée.",
        )
    width = max(len(installed), len(bundled))
    installed_comparable = installed + (0,) * (width - len(installed))
    bundled_comparable = bundled + (0,) * (width - len(bundled))
    if installed_comparable < bundled_comparable:
        return StreamDeckPluginHealth(
            "outdated",
            installed_version,
            bundled_version,
            True,
            f"Plugin installé {installed_version}, version fournie {bundled_version} : mise à jour recommandée.",
        )
    if installed_comparable > bundled_comparable:
        return StreamDeckPluginHealth(
            "newer",
            installed_version,
            bundled_version,
            False,
            f"Le plugin installé ({installed_version}) est plus récent que celui fourni ({bundled_version}).",
        )
    return StreamDeckPluginHealth(
        "current",
        installed_version,
        bundled_version,
        False,
        f"Le plugin Stream Deck {installed_version} est à jour.",
    )

