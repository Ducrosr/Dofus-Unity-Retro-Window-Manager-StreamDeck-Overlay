from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from dwm.services.obs_overlay_capture import _ensure_obs_popup_window


class ObsOverlayCaptureTests(unittest.TestCase):
    def test_simulation_overlay_never_creates_obs_popup_surface(self) -> None:
        overlay = SimpleNamespace(
            obs_capture=False,
            _closed=False,
            toast_window=None,
            root=Mock(),
        )
        ui = SimpleNamespace(Toplevel=Mock(), _apply_non_activating_style=Mock())

        self.assertIsNone(_ensure_obs_popup_window(overlay, ui))
        ui.Toplevel.assert_not_called()

    def test_closed_production_overlay_never_recreates_popup(self) -> None:
        overlay = SimpleNamespace(
            obs_capture=True,
            _closed=True,
            toast_window=None,
            root=Mock(),
        )
        ui = SimpleNamespace(Toplevel=Mock(), _apply_non_activating_style=Mock())

        self.assertIsNone(_ensure_obs_popup_window(overlay, ui))
        ui.Toplevel.assert_not_called()

    def test_production_overlay_reuses_existing_popup_toplevel(self) -> None:
        window = Mock()
        window.winfo_exists.return_value = 1
        overlay = SimpleNamespace(
            obs_capture=True,
            _closed=False,
            toast_window=window,
            root=Mock(),
        )
        ui = SimpleNamespace(Toplevel=Mock(), _apply_non_activating_style=Mock())

        self.assertIs(_ensure_obs_popup_window(overlay, ui), window)
        ui.Toplevel.assert_not_called()

    def test_new_production_popup_is_explicitly_owned(self) -> None:
        window = Mock()
        ui = SimpleNamespace(
            Toplevel=Mock(return_value=window),
            _apply_non_activating_style=Mock(),
        )
        overlay = SimpleNamespace(
            obs_capture=True,
            _closed=False,
            toast_window=None,
            root=Mock(),
        )

        with patch(
            "dwm.services.obs_overlay_capture._clear_toolwindow_style"
        ):
            result = _ensure_obs_popup_window(overlay, ui)

        self.assertIs(result, window)
        self.assertIs(overlay.toast_window, window)
        self.assertTrue(window._dwm_obs_capture)
        ui.Toplevel.assert_called_once_with(overlay.root)


if __name__ == "__main__":
    unittest.main()
