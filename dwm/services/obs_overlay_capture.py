from __future__ import annotations

import ctypes
import os
from ctypes import wintypes


OVERLAY_WINDOW_TITLE = "Dofus Window Manager — Overlay"


def _clear_toolwindow_style(window) -> None:
    """Remove WS_EX_TOOLWINDOW so OBS can enumerate the persistent overlay."""
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
        # This is a compatibility enhancement only; never prevent the overlay
        # from being shown if Windows rejects a style update.
        return


def enable_obs_overlay_capture() -> None:
    """Keep the existing overlay behaviour while making it capturable by OBS.

    ``ui_overlays._apply_non_activating_style`` intentionally marks the
    persistent overlay as ``WS_EX_TOOLWINDOW``. OBS filters tool windows from
    its window-capture picker, so wrap the existing style helper and remove
    only that flag after its normal focus/click-through settings are applied.
    """
    from dwm import ui_overlays

    original = ui_overlays._apply_non_activating_style
    if getattr(original, "_dwm_obs_capture_wrapper", False):
        return

    def apply_obs_compatible_style(window, *, click_through: bool) -> None:
        original(window, click_through=click_through)
        try:
            window.title(OVERLAY_WINDOW_TITLE)
        except Exception:
            pass
        _clear_toolwindow_style(window)

    setattr(apply_obs_compatible_style, "_dwm_obs_capture_wrapper", True)
    ui_overlays._apply_non_activating_style = apply_obs_compatible_style
