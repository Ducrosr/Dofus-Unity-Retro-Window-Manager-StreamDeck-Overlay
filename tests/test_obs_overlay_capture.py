from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from dwm.services.obs_overlay_capture import _ensure_obs_popup_window
from dwm.ui_overlays import DEFAULT_PALETTE, OverlayUI


class _FakeWindow:
    def __init__(self) -> None:
        self.destroyed = False
        self.children = []

    def winfo_exists(self):
        return not self.destroyed

    def winfo_children(self):
        return tuple(self.children)

    def withdraw(self):
        pass

    def title(self, _value):
        pass

    def overrideredirect(self, _value):
        pass

    def attributes(self, *_args):
        pass

    def configure(self, **_kwargs):
        pass

    def geometry(self, _value):
        pass

    def update_idletasks(self):
        pass

    def deiconify(self):
        pass

    def destroy(self):
        self.destroyed = True


class OBSOverlayLifecycleTests(unittest.TestCase):
    def test_popup_owner_reuses_same_window_until_terminal_close(self) -> None:
        created: list[_FakeWindow] = []
        fake_module = SimpleNamespace(
            Toplevel=lambda _root: created.append(_FakeWindow()) or created[-1],
            _apply_non_activating_style=lambda *_args, **_kwargs: None,
        )
        overlay = SimpleNamespace(
            root=object(),
            toast_window=None,
            obs_capture_enabled=True,
            _closed=False,
        )

        with patch("dwm.services.obs_overlay_capture._clear_toolwindow_style"):
            first = _ensure_obs_popup_window(overlay, fake_module)
            second = _ensure_obs_popup_window(overlay, fake_module)
            overlay._closed = True
            closed = _ensure_obs_popup_window(overlay, fake_module)

        self.assertIs(first, second)
        self.assertEqual(len(created), 1)
        self.assertIsNone(closed)

    def test_simulation_never_creates_obs_popup(self) -> None:
        factory = Mock()
        fake_module = SimpleNamespace(
            Toplevel=factory,
            _apply_non_activating_style=lambda *_args, **_kwargs: None,
        )
        overlay = SimpleNamespace(
            root=object(),
            toast_window=None,
            obs_capture_enabled=False,
            _closed=False,
        )

        self.assertIsNone(_ensure_obs_popup_window(overlay, fake_module))
        factory.assert_not_called()

    def test_palette_refresh_keeps_persistent_toplevel_identity(self) -> None:
        overlay = OverlayUI.__new__(OverlayUI)
        overlay.palette = dict(DEFAULT_PALETTE)
        overlay.persistent_window = Mock()
        overlay.persistent_enabled = True
        overlay.persistent_opacity = 88
        overlay.persistent_locked = False
        overlay.compact_window = None
        overlay._render_persistent = Mock()
        overlay._refresh_compact = Mock()
        original = overlay.persistent_window

        with patch("dwm.ui_overlays._apply_non_activating_style"):
            overlay.set_palette({"accent": "#123456"})

        self.assertIs(overlay.persistent_window, original)
        overlay._render_persistent.assert_called_once()

    def test_close_all_is_terminal_and_idempotent(self) -> None:
        overlay = OverlayUI.__new__(OverlayUI)
        overlay._closed = False
        overlay.hide_swap_notification = Mock()
        overlay._destroy_persistent = Mock()
        overlay.close_compact = Mock()

        overlay.close_all()
        overlay.close_all()

        self.assertTrue(overlay._closed)
        overlay.hide_swap_notification.assert_called_once()
        overlay._destroy_persistent.assert_called_once()
        overlay.close_compact.assert_called_once_with(show_root=False)


if __name__ == "__main__":
    unittest.main()
