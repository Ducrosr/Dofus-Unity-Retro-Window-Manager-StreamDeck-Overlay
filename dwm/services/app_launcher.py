from __future__ import annotations

import json
import sys
from pathlib import Path

from ..utils.paths import application_dir


LAUNCHER_DESCRIPTOR_NAME = "streamdeck-launcher.json"


def build_launcher_descriptor(
    *,
    frozen: bool | None = None,
    executable: str | Path | None = None,
    app_dir: str | Path | None = None,
) -> dict[str, object]:
    """Describe how Stream Deck can reopen this exact application install."""
    is_frozen = bool(getattr(sys, "frozen", False)) if frozen is None else bool(frozen)
    executable_path = Path(executable or sys.executable).resolve()
    application_root = Path(app_dir or application_dir()).resolve()
    arguments: list[str] = ["--use-saved-mode"] if is_frozen else [
        str(application_root / "main.py"),
        "--use-saved-mode",
    ]
    return {
        "version": 1,
        "executable": str(executable_path),
        "arguments": arguments,
        "working_directory": str(application_root),
    }


def register_current_launcher(data_root: Path) -> Path:
    """Atomically register the current source checkout or packaged executable."""
    descriptor_path = data_root / LAUNCHER_DESCRIPTOR_NAME
    temporary_path = descriptor_path.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(build_launcher_descriptor(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(descriptor_path)
    return descriptor_path
