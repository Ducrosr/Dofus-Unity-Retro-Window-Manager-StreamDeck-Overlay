from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from .i18n import tr


class TrayController:
    """Small optional pystray wrapper kept outside the Tk application."""

    def __init__(self, icon_path: str | Path) -> None:
        self.icon_path = Path(icon_path)
        self._icon = None

    @property
    def is_running(self) -> bool:
        return self._icon is not None

    def start(
        self,
        *,
        show: Callable[[], None],
        refresh: Callable[[], None],
        quit_app: Callable[[], None],
        toggle_hotkeys: Callable[[], None] | None = None,
    ) -> bool:
        if self._icon is not None:
            return True
        if sys.platform != "win32":
            return False

        try:
            import pystray
            from PIL import Image

            image = Image.open(self.icon_path)
            menu = pystray.Menu(
                pystray.MenuItem(lambda _item: tr("Afficher Dofus Window Manager"), lambda _icon, _item: show(), default=True),
                pystray.MenuItem(lambda _item: tr("Actualiser les fenêtres"), lambda _icon, _item: refresh()),
                pystray.MenuItem(lambda _item: tr("Suspendre / reprendre les raccourcis"), lambda _icon, _item: toggle_hotkeys() if toggle_hotkeys else None, enabled=toggle_hotkeys is not None),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(lambda _item: tr("Quitter"), lambda _icon, _item: quit_app()),
            )
            icon = pystray.Icon("DofusWindowManager", image, "Dofus Window Manager", menu)
            icon.run_detached()
            self._icon = icon
            return True
        except Exception:
            self._icon = None
            return False

    def notify(self, message: str, title: str = "Dofus Window Manager") -> None:
        icon = self._icon
        if icon is None:
            return
        try:
            icon.notify(message, title)
        except Exception:
            pass

    def stop(self) -> None:
        icon = self._icon
        self._icon = None
        if icon is None:
            return
        try:
            icon.stop()
        except Exception:
            pass
