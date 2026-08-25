from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping

from ..storage.atomic import atomic_write_text


SNAPSHOT_PREFIX = "DWM_snapshot_"
DEFAULT_SNAPSHOT_LIMIT = 12


def _safe_reason(reason: object) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", str(reason or "manuel").casefold()).strip("-")
    return normalized[:36] or "manuel"


@dataclass(frozen=True)
class BackupSnapshot:
    path: Path
    created_at: str
    reason: str
    app_version: str

    @property
    def label(self) -> str:
        try:
            created = datetime.fromisoformat(self.created_at).strftime("%d/%m/%Y %H:%M:%S")
        except ValueError:
            created = self.created_at or self.path.stem
        return f"{created} · {self.reason} · v{self.app_version}"


def list_backup_snapshots(backups_dir: str | Path) -> list[BackupSnapshot]:
    directory = Path(backups_dir)
    if not directory.exists():
        return []
    snapshots: list[BackupSnapshot] = []
    for path in directory.glob(f"{SNAPSHOT_PREFIX}*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            metadata = data.get("snapshot_metadata") or {}
            created_at = str(metadata.get("created_at") or data.get("exported_at") or "")
            reason = str(metadata.get("reason") or "automatique")
            app_version = str(metadata.get("app_version") or data.get("app_version") or "?")
            if not created_at:
                raise ValueError("date absente")
        except (OSError, ValueError, json.JSONDecodeError, AttributeError):
            continue
        snapshots.append(BackupSnapshot(path, created_at, reason, app_version))
    return sorted(snapshots, key=lambda snapshot: snapshot.created_at, reverse=True)


def create_backup_snapshot(
    backups_dir: str | Path,
    backup: Mapping[str, object],
    *,
    reason: str,
    app_version: str,
    keep: int = DEFAULT_SNAPSHOT_LIMIT,
    now: datetime | None = None,
) -> BackupSnapshot:
    directory = Path(backups_dir)
    directory.mkdir(parents=True, exist_ok=True)
    created = now or datetime.now()
    created_at = created.isoformat(timespec="microseconds")
    safe_reason = _safe_reason(reason)
    filename = f"{SNAPSHOT_PREFIX}{created:%Y%m%d_%H%M%S_%f}_{safe_reason}.json"
    path = directory / filename
    payload = dict(backup)
    payload["snapshot_metadata"] = {
        "created_at": created_at,
        "reason": str(reason or "manuel"),
        "app_version": app_version,
    }
    atomic_write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

    snapshots = list_backup_snapshots(directory)
    for obsolete in snapshots[max(1, int(keep)) :]:
        try:
            obsolete.path.unlink(missing_ok=True)
        except OSError:
            pass
    return BackupSnapshot(path, created_at, str(reason or "manuel"), app_version)


def load_backup_snapshot(snapshot: BackupSnapshot | str | Path) -> dict[str, object]:
    path = snapshot.path if isinstance(snapshot, BackupSnapshot) else Path(snapshot)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Le point de restauration est invalide.")
    return data
