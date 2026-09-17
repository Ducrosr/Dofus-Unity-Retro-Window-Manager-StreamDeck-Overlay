from __future__ import annotations

import ctypes
import os
from ctypes import wintypes


OVERLAY_WINDOW_TITLE = "Dofus Window Manager — Overlay"
POPUP_WINDOW_TITLE = "Dofus Window Manager — Focus Popup"
POPUP_IDLE_GEOMETRY = "320x100+0+0"


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


def _ensure_obs_popup_window(overlay, ui_overlays):
    """Create one permanent, transparent popup HWND for OBS to keep attached to."""
    window = overlay.toast_window
    if window is not None:
        try:
            if window.winfo_exists():
                return window
        except Exception:
            pass

    window = ui_overlays.Toplevel(overlay.root)
    overlay.toast_window = window
    window.withdraw()
    _set_window_title(window, POPUP_WINDOW_TITLE)
    window.overrideredirect(True)
    window.attributes("-topmost", True)
    window.attributes("-alpha", 0.0)
    window.configure(background=overlay.palette["accent"])
    window.geometry(POPUP_IDLE_GEOMETRY)
    window.update_idletasks()
    ui_overlays._apply_non_activating_style(window, click_through=True)
    _clear_toolwindow_style(window)
    window.deiconify()
    return window


def enable_obs_overlay_capture() -> None:
    """Make both persistent overlay windows discoverable and stable for OBS.

    The regular character list and the focus notification are distinct Tk/Win32
    windows. OBS therefore captures them separately. The focus notification is
    kept alive for the whole application session with alpha 0 while idle, so
    OBS keeps the same HWND instead of having to reacquire a newly created
    window after every character switch.
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

    init_original = ui_overlays.OverlayUI.__init__
    if not getattr(init_original, "_dwm_obs_capture_wrapper", False):

        def init_obs_overlay(self, *args, **kwargs) -> None:
            init_original(self, *args, **kwargs)
            _ensure_obs_popup_window(self, ui_overlays)

        init_obs_overlay._dwm_obs_capture_wrapper = True
        ui_overlays.OverlayUI.__init__ = init_obs_overlay

    hide_original = ui_overlays.OverlayUI._hide_visible_toast
    if not getattr(hide_original, "_dwm_obs_capture_wrapper", False):

        def hide_obs_focus_popup(self) -> None:
            if self.toast_job is not None:
                try:
                    self.root.after_cancel(self.toast_job)
                except Exception:
                    pass
                self.toast_job = None

            window = _ensure_obs_popup_window(self, ui_overlays)
            try:
                window.attributes("-alpha", 0.0)
                _set_window_title(window, POPUP_WINDOW_TITLE)
                _clear_toolwindow_style(window)
                window.deiconify()
            except Exception:
                pass
            self._toast_images.clear()

        hide_obs_focus_popup._dwm_obs_capture_wrapper = True
        ui_overlays.OverlayUI._hide_visible_toast = hide_obs_focus_popup

    popup_original = ui_overlays.OverlayUI._show_swap_notification_now
    if not getattr(popup_original, "_dwm_obs_capture_wrapper", False):

        def show_obs_focus_popup(self, request) -> None:
            window = _ensure_obs_popup_window(self, ui_overlays)
            for child in tuple(window.winfo_children()):
                try:
                    child.destroy()
                except Exception:
                    pass

            toplevel_original = ui_overlays.Toplevel

            def reuse_popup_window(_root):
                return window

            ui_overlays.Toplevel = reuse_popup_window
            try:
                popup_original(self, request)
            finally:
                ui_overlays.Toplevel = toplevel_original

            _set_window_title(window, POPUP_WINDOW_TITLE)
            _clear_toolwindow_style(window)

        show_obs_focus_popup._dwm_obs_capture_wrapper = True
        ui_overlays.OverlayUI._show_swap_notification_now = show_obs_focus_popup

    close_original = ui_overlays.OverlayUI.close_all
    if not getattr(close_original, "_dwm_obs_capture_wrapper", False):

        def close_obs_overlay(self) -> None:
            window = self.toast_window
            close_original(self)
            self.toast_window = None
            if window is not None:
                try:
                    window.destroy()
                except Exception:
                    pass

        close_obs_overlay._dwm_obs_capture_wrapper = True
        ui_overlays.OverlayUI.close_all = close_obs_overlay
