import os
import sys
from pathlib import Path

APP_NAME = "DofusUnityWindowManager"


def application_dir() -> Path:
    """Return the directory containing the source entry point or packaged exe."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent


def resource_path(*relative_parts: str) -> str:
    """Return absolute path to a bundled resource (icons, etc.).

    Works both in dev mode and in PyInstaller onefile mode.
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return str(Path(base).joinpath(*relative_parts))
    return str(application_dir().joinpath(*relative_parts))


def app_data_dir() -> Path:
    """A writable directory for settings/logs/profiles."""
    # Prefer %APPDATA% (Roaming) because profiles/settings are user-level.
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / APP_NAME
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / APP_NAME
    # Fallback: current working directory
    return Path.cwd() / APP_NAME


def ensure_dirs() -> dict:
    root = app_data_dir()
    profiles = root / "profiles"
    logs = root / "logs"
    backups = root / "backups"
    root.mkdir(parents=True, exist_ok=True)
    profiles.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    backups.mkdir(parents=True, exist_ok=True)
    return {"root": root, "profiles": profiles, "logs": logs, "backups": backups}
