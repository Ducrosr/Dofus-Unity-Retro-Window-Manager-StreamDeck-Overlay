from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import ModuleType

from ..utils.paths import application_dir


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE_NAME = "DofusWindowManager"


def build_startup_command(
    *,
    frozen: bool | None = None,
    executable: str | Path | None = None,
    app_dir: str | Path | None = None,
) -> str:
    """Build the per-user startup command for this exact installation."""
    is_frozen = bool(getattr(sys, "frozen", False)) if frozen is None else bool(frozen)
    executable_path = Path(executable or sys.executable).resolve()
    application_root = Path(app_dir or application_dir()).resolve()

    if is_frozen:
        arguments = [str(executable_path), "--use-saved-mode", "--minimized"]
    else:
        pythonw = executable_path.with_name("pythonw.exe")
        launcher = pythonw if executable_path.name.lower() in {"python.exe", "pythonw.exe"} else executable_path
        arguments = [
            str(launcher),
            str(application_root / "main.py"),
            "--use-saved-mode",
            "--minimized",
        ]
    return subprocess.list2cmdline(arguments)


def set_startup_enabled(
    enabled: bool,
    *,
    registry_module: ModuleType | None = None,
    command: str | None = None,
) -> None:
    """Enable or disable startup for the current Windows user."""
    registry = registry_module
    if registry is None:
        if sys.platform != "win32":
            raise OSError("Le démarrage automatique est disponible uniquement sous Windows.")
        import winreg

        registry = winreg

    access = registry.KEY_SET_VALUE
    with registry.OpenKey(registry.HKEY_CURRENT_USER, RUN_KEY, 0, access) as key:
        if enabled:
            registry.SetValueEx(
                key,
                RUN_VALUE_NAME,
                0,
                registry.REG_SZ,
                command or build_startup_command(),
            )
            return
        try:
            registry.DeleteValue(key, RUN_VALUE_NAME)
        except FileNotFoundError:
            pass
