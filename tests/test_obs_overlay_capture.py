from __future__ import annotations

import unittest
from unittest.mock import Mock

from dwm.services.obs_overlay_capture import _ensure_obs_popup_window
from dwm.ui_overlays import OverlayUI


class _FakeWindow:
    def __init__(self) -> None:
        self.destroyed = False
        self.children: list[object] = []
        self.titles: list[str] = []
        self.geometries: list[str] = []

    def winfo_exists(self) -> bool:
        return not self.destroyed

    def winfo_children(self):
        return tuple(self.children)

    def destroy(self) -> None:
        self.destroyed = True

    def withdraw(self) -> None:
        pass

    def title(self, value: str) -> None:
        self.titles.append(value)

    def overrideredirect(self, _value: bool) -> None:
        pass

    def attributes(self, *_args) -> None:
        pass

    def configure(self, **_kwargs) -> None:
        pass

    def geometry(self, value: str) -> None:
        self.geometries.append(value)

    def update_idletasks(self) -> None:
        pass

    def deiconify(self) -> None:
        pass


class _FakeOverlay:
    def __init__(self, *, capture_for_obs: bool = True) -> None:
        self.capture_for_obs = capture_for_obs
        self._closed = False
        self.toast_window = None
        self.created = 0
        self.styled: list[tuple[object, bool]] = []

    def _create_toast_window(self):
        self.created += 1
        self.toast_window = _FakeWindow()
        return self.toast_window

    def _destroy_toast_window(self) -> None:
        window = self.toast_window
        self.toast_window = None
        if window is not None:
            window.destroy()

    def _apply_window_style(self, window, *, click_through: bool) -> None:
        self.styled.append((window, click_through))


class OBSOverlayLifecycleTests(unittest.TestCase):
    def test_production_popup_reuses_one_owned_window(self) -> None:
        overlay = _FakeOverlay()

        first = _ensure_obs_popup_window(overlay)
        second = _ensure_obs_popup_window(overlay)

        self.assertIs(first, second)
        self.assertEqual(overlay.created, 1)
        self.assertEqual(overlay.styled, [(first, True)])

    def test_simulation_and_closed_overlay_do_not_create_obs_popup(self) -> None:
        simulation = _FakeOverlay(capture_for_obs=False)
        self.assertIsNone(_ensure_obs_popup_window(simulation))
        self.assertEqual(simulation.created, 0)

        production = _FakeOverlay()
        production._closed = True
        self.assertIsNone(_ensure_obs_popup_window(production))
        self.assertEqual(production.created, 0)

    def test_palette_change_keeps_persistent_toplevel(self) -> None:
        overlay = OverlayUI.__new__(OverlayUI)
        overlay._closed = False
        overlay.palette = {}
        overlay.persistent_window = object()
        overlay.persistent_enabled = True
        overlay.compact_window = None
        overlay._render_persistent = Mock()
        overlay._refresh_compact = Mock()
        original_window = overlay.persistent_window

        overlay.set_palette({"bg": "#000000"})

        self.assertIs(overlay.persistent_window, original_window)
        overlay._render_persistent.assert_called_once()

    def test_lock_change_renders_in_place_without_destroying_persistent_window(self) -> None:
        overlay = OverlayUI.__new__(OverlayUI)
        overlay._closed = False
        overlay.root = Mock()
        overlay.persistent_locked = False
        overlay._monitor_job = "existing"
        overlay._ensure_persistent = Mock()
        overlay._render_persistent = Mock()
        overlay._destroy_persistent = Mock()

        overlay.configure_persistent(
            enabled=True,
            x=10,
            y=20,
            opacity=88,
            locked=True,
        )

        overlay._destroy_persistent.assert_not_called()
        overlay._ensure_persistent.assert_called_once()
        overlay._render_persistent.assert_called_once()

    def test_terminal_close_is_idempotent(self) -> None:
        overlay = OverlayUI.__new__(OverlayUI)
        overlay._closed = False
        overlay.toast_show_job = None
        overlay.toast_job = None
        overlay._toast_request = object()
        overlay._destroy_toast_window = Mock()
        overlay._destroy_persistent = Mock()
        overlay.close_compact = Mock()

        overlay.close_all()
        overlay.close_all()

        overlay._destroy_toast_window.assert_called_once()
        overlay._destroy_persistent.assert_called_once()
        overlay.close_compact.assert_called_once_with(show_root=False)


if __name__ == "__main__":
    unittest.main()
