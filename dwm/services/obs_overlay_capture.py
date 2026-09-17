from __future__ import annotations

import ctypes
import os
from ctypes import wintypes


OVERLAY_WINDOW_TITLE = "Dofus Window Manager — Overlay"
POPUP_WINDOW_TITLE = "Dofus Window Manager — Focus Popup"


def _set_window_title(window, title: str) -> None:
    try:
        window.title(title)
    except Exception:
        return


def _clear_toolwindow_style(window) -> None:
    """Remove WS_EX_TOOLWINDOW so OBS can enumerate the DWM overlay windows."""
    if os.name != "nt":
        return

    try:
        window.update_idletasks()
        user32 = ctypes.windll.user32
        raw_hwnd = wintypes.HWND(int(window.winfo_id()))

        user32.GetAncestor.argtypes = (wintypes.HWND, wintypes.UINT)
        user32.GetAncestor.restype = wintypes.HWND
        hwnd = user32.GetAncestor(raw_hwnd, 2) or raw_hwnd  # GA_ROOT

        getter = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
        setter = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
        getter.argtypes = (wintypes.HWND, ctypes.c_int)
        getter.restype = ctypes.c_ssize_t
        setter.argtypes = (wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t)
        setter.restype = ctypes.c_ssize_t

        gwl_exstyle = -20
        ws_ex_toolwindow = 0x00000080
        style = int(getter(hwnd, gwl_exstyle))
        updated_style = style & ~ws_ex_toolwindow
        if updated_style != style:
            setter(hwnd, gwl_exstyle, updated_style)

        hwnd_topmost = wintypes.HWND(-1)
        swp_nomove = 0x0002
        swp_nosize = 0x0001
        swp_noactivate = 0x0010
        swp_showwindow = 0x0040
        swp_framechanged = 0x0020
        user32.SetWindowPos.argtypes = (
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        )
        user32.SetWindowPos.restype = wintypes.BOOL
        user32.SetWindowPos(
            hwnd,
            hwnd_topmost,
            0,
            0,
            0,
            0,
            swp_nomove | swp_nosize | swp_noactivate | swp_showwindow | swp_framechanged,
        )
    except Exception:
        # OBS compatibility must never prevent the overlay from being shown.
        return


def enable_obs_overlay_capture() -> None:
    """Make both persistent overlay windows discoverable by OBS.

    The regular persistent character list and the short focus notification are
    distinct Tk/Win32 windows. OBS must therefore be able to enumerate each one
    independently. Keep the existing non-activating/click-through behaviour,
    remove only ``WS_EX_TOOLWINDOW``, and give both windows stable titles so an
    OBS Window Capture source can reacquire them by title/executable.
    """
    from dwm import ui_overlays

    style_original = ui_overlays._apply_non_activating_style
    if not getattr(style_original, "_dwm_obs_capture_wrapper", False):

        def apply_obs_compatible_style(window, *, click_through: bool) -> None:
            style_original(window, click_through=click_through)
            _clear_toolwindow_style(window)

        apply_obs_compatible_style._dwm_obs_capture_wrapper = True
        ui_overlays._apply_non_activating_style = apply_obs_compatible_style

    ensure_original = ui_overlays.OverlayUI._ensure_persistent
    if not getattr(ensure_original, "_dwm_obs_capture_wrapper", False):

        def ensure_obs_persistent(self) -> None:
            ensure_original(self)
            window = self.persistent_window
            if window is not None:
                _set_window_title(window, OVERLAY_WINDOW_TITLE)
                _clear_toolwindow_style(window)

        ensure_obs_persistent._dwm_obs_capture_wrapper = True
        ui_overlays.OverlayUI._ensure_persistent = ensure_obs_persistent

    popup_original = ui_overlays.OverlayUI._show_swap_notification_now
    if not getattr(popup_original, "_dwm_obs_capture_wrapper", False):

        def show_obs_focus_popup(self, request) -> None:
            popup_original(self, request)
            window = self.toast_window
            if window is not None:
                _set_window_title(window, POPUP_WINDOW_TITLE)
                _clear_toolwindow_style(window)

        show_obs_focus_popup._dwm_obs_capture_wrapper = True
        ui_overlays.OverlayUI._show_swap_notification_now = show_obs_focus_popup
