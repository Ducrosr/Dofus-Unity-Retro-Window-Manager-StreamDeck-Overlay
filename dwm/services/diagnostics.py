from __future__ import annotations

import json
import os
import time
import zipfile
from collections.abc import Iterable
from pathlib import Path


PLUGIN_DIRECTORY_NAME = "com.remyducros.dofuswindowmanager.sdPlugin"


def installed_plugin_manifest(appdata: str | Path | None = None) -> Path:
    base = Path(appdata or os.environ.get("APPDATA") or "")
    return base / "Elgato" / "StreamDeck" / "Plugins" / PLUGIN_DIRECTORY_NAME / "manifest.json"


def read_manifest_version(path: str | Path) -> str | None:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    version = str(data.get("Version") or "").strip()
    return version or None


def read_packaged_plugin_version(path: str | Path) -> str | None:
    try:
        with zipfile.ZipFile(path) as archive:
            manifest_name = next(
                name
                for name in archive.namelist()
                if name == f"{PLUGIN_DIRECTORY_NAME}/manifest.json"
                or name.endswith(f"/{PLUGIN_DIRECTORY_NAME}/manifest.json")
            )
            data = json.loads(archive.read(manifest_name).decode("utf-8"))
    except (OSError, StopIteration, UnicodeDecodeError, zipfile.BadZipFile, json.JSONDecodeError):
        return None
    version = str(data.get("Version") or "").strip()
    return version or None


def format_activity(last_request_at: float | None, *, now: float | None = None) -> str:
    if last_request_at is None:
        return "aucune requête reçue"
    age = max(0, int((time.time() if now is None else now) - last_request_at))
    if age < 3:
        return "à l’instant"
    if age < 60:
        return f"il y a {age} s"
    return f"il y a {age // 60} min"


def build_diagnostic_report(rows: Iterable[tuple[str, object]]) -> str:
    lines = ["Dofus Window Manager — rapport de diagnostic", ""]
    lines.extend(f"{label}: {value}" for label, value in rows)
    return "\n".join(lines) + "\n"
