from __future__ import annotations

import os
import sys
from collections.abc import Callable
from pathlib import Path

from ..utils.paths import resource_path


STREAMDECK_PLUGIN_FILENAME = "com.remyducros.dofuswindowmanager.streamDeckPlugin"


def bundled_streamdeck_plugin_path() -> Path:
    path = Path(resource_path("streamdeck-plugin", STREAMDECK_PLUGIN_FILENAME))
    if not path.is_file():
        raise FileNotFoundError(f"Paquet Stream Deck introuvable : {path}")
    return path


def open_streamdeck_plugin(
    plugin_path: Path | None = None,
    *,
    opener: Callable[[str], object] | None = None,
) -> Path:
    """Open the plugin package with Stream Deck's Windows file association."""
    path = plugin_path or bundled_streamdeck_plugin_path()
    if not path.is_file():
        raise FileNotFoundError(f"Paquet Stream Deck introuvable : {path}")

    if opener is None:
        if sys.platform != "win32":
            raise OSError("L'installation intégrée du plugin est disponible uniquement sous Windows.")
        opener = getattr(os, "startfile", None)
        if opener is None:
            raise OSError("Windows ne permet pas d'ouvrir le paquet Stream Deck.")

    opener(str(path))
    return path
