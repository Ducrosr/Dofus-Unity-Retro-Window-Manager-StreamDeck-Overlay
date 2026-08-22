from __future__ import annotations

import json
import pickle
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

PROFILE_SCHEMA_VERSION = 1


class _LegacyProfileUnpickler(pickle.Unpickler):
    """Load primitive legacy profile data without allowing global objects."""

    def find_class(self, module: str, name: str):
        raise pickle.UnpicklingError(f"objet pickle interdit: {module}.{name}")


def _safe_name(name: str) -> str:
    n = (name or "").strip()
    n = re.sub(r"[\\/:*?\"<>|]", "_", n)
    n = re.sub(r"\s+", " ", n)
    return n[:80] or "profile"


@dataclass
class Profile:
    name: str
    order: List[str]
    aliases: Dict[str, str]
    created_at: str
    updated_at: str

    def to_dict(self) -> dict:
        return {
            "schema_version": PROFILE_SCHEMA_VERSION,
            "name": self.name,
            "order": list(self.order),
            "aliases": dict(self.aliases),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(d: dict) -> "Profile":
        now = datetime.now().isoformat(timespec="seconds")
        return Profile(
            name=d.get("name", ""),
            order=list(d.get("order", []) or []),
            aliases=dict(d.get("aliases", {}) or {}),
            created_at=d.get("created_at", now),
            updated_at=d.get("updated_at", now),
        )


def profile_path(profiles_dir: Path, name: str) -> Path:
    safe = _safe_name(name)
    return profiles_dir / f"{safe}.json"


def list_profiles(profiles_dir: Path) -> List[str]:
    profiles_dir.mkdir(parents=True, exist_ok=True)
    names = []
    for p in profiles_dir.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            names.append(str(data.get("name") or p.stem))
        except Exception:
            names.append(p.stem)
    return sorted(set(names), key=str.lower)


def load_profile(profiles_dir: Path, name: str) -> Profile:
    p = profile_path(profiles_dir, name)
    data = json.loads(p.read_text(encoding="utf-8"))
    pr = Profile.from_dict(data)
    if not pr.name:
        pr.name = p.stem
    return pr


def save_profile(profiles_dir: Path, profile: Profile) -> None:
    profiles_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now().isoformat(timespec="seconds")
    if not profile.created_at:
        profile.created_at = now
    profile.updated_at = now
    path = profile_path(profiles_dir, profile.name)
    path.write_text(json.dumps(profile.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


def delete_profile(profiles_dir: Path, name: str) -> None:
    p = profile_path(profiles_dir, name)
    if p.exists():
        p.unlink()


def migrate_pickles(formation_dir: Path, profiles_dir: Path) -> List[str]:
    """Convert legacy .pkl profiles to JSON.

    Only call this for profiles created locally by an older version. Pickle
    files from an untrusted source can execute code while being loaded.

    Returns the list of migrated profile names.
    """
    migrated = []
    if not formation_dir.exists():
        return migrated

    for pkl in formation_dir.glob("*.pkl"):
        try:
            with pkl.open("rb") as f:
                data = _LegacyProfileUnpickler(f).load()
            order = data.get("order", []) if isinstance(data, dict) else []
            aliases = data.get("aliases", {}) if isinstance(data, dict) else {}
            name = pkl.stem

            # Do not overwrite existing JSON
            dest = profile_path(profiles_dir, name)
            if dest.exists():
                continue

            now = datetime.now().isoformat(timespec="seconds")
            pr = Profile(name=name, order=list(order), aliases=dict(aliases), created_at=now, updated_at=now)
            save_profile(profiles_dir, pr)
            migrated.append(pr.name)
        except Exception:
            continue

    return migrated
