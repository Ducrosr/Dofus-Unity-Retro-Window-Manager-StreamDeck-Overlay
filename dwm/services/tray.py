from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from .i18n import tr


@dataclass(frozen=True)
class TrayState:
    profiles: tuple[str, ...] = ()
    active_profile: str = ""
    game_mode: str = "unity"
    overlay_enabled: bool = False
    hotkeys_paused: bool = False
    enabled: bool = True
    language: str = "fr"


class TrayController:
    """Small optional pystray wrapper kept outside the Tk application."""

    def __init__(self, icon_path: str | Path) -> None:
        self.icon_path = Path(icon_path)
        self._icon = None
        self._state = TrayState()

    def set_state(self, state: TrayState) -> None:
        """Publish an immutable UI snapshot; menu callbacks never access Tk."""
        if state == self._state:
            return
        self._state = state
        if self._icon is not None:
            try:
                self._icon.update_menu()
            except Exception:
                pass

    def _build_menu(self, pystray, *, show, refresh, quit_app, toggle_hotkeys,
                    select_profile, select_mode, toggle_overlay):
        def profile_item(name):
            return pystray.MenuItem(
                name, lambda _icon, _item: select_profile(name),
                checked=lambda _item: self._state.active_profile == name, radio=True,
            )

        def mode_item(mode, label):
            return pystray.MenuItem(
                label, lambda _icon, _item: select_mode(mode),
                checked=lambda _item: self._state.game_mode == mode, radio=True,
            )

        return pystray.Menu(
            pystray.MenuItem(lambda _item: tr("Afficher Dofus Window Manager"), lambda _icon, _item: show(), default=True),
            pystray.MenuItem(
                lambda _item: tr("Profils"),
                pystray.Menu(lambda: tuple(profile_item(name) for name in self._state.profiles)),
                enabled=lambda _item: self._state.enabled and bool(self._state.profiles) and select_profile is not None,
            ),
            pystray.MenuItem(
                lambda _item: tr("Version de Dofus"),
                pystray.Menu(mode_item("unity", "Unity"), mode_item("retro", "Retro")),
                enabled=lambda _item: self._state.enabled and select_mode is not None,
            ),
            pystray.MenuItem(
                lambda _item: tr("Afficher l’overlay"), lambda _icon, _item: toggle_overlay(),
                checked=lambda _item: self._state.overlay_enabled,
                enabled=lambda _item: self._state.enabled and toggle_overlay is not None,
            ),
            pystray.MenuItem(lambda _item: tr("Actualiser les fenêtres"), lambda _icon, _item: refresh()),
            pystray.MenuItem(
                lambda _item: tr("Reprendre les raccourcis") if self._state.hotkeys_paused else tr("Suspendre les raccourcis"),
                lambda _icon, _item: toggle_hotkeys() if toggle_hotkeys else None,
                enabled=lambda _item: self._state.enabled and toggle_hotkeys is not None,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda _item: tr("Quitter"), lambda _icon, _item: quit_app()),
        )

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
        select_profile: Callable[[str], None] | None = None,
        select_mode: Callable[[str], None] | None = None,
        toggle_overlay: Callable[[], None] | None = None,
    ) -> bool:
        if self._icon is not None:
            return True
        if sys.platform != "win32":
            return False

        try:
            import pystray
            from PIL import Image

            image = Image.open(self.icon_path)
            menu = self._build_menu(
                pystray, show=show, refresh=refresh, quit_app=quit_app,
                toggle_hotkeys=toggle_hotkeys, select_profile=select_profile,
                select_mode=select_mode, toggle_overlay=toggle_overlay,
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
