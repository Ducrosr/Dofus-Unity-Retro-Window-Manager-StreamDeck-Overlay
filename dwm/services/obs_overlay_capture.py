from __future__ import annotations

import ctypes
import os
from ctypes import wintypes


OVERLAY_WINDOW_TITLE = "Dofus Window Manager — Overlay"
POPUP_WINDOW_TITLE = "Dofus Window Manager — Focus Popup"
POPUP_IDLE_GEOMETRY = "320x100+0+0"
POPUP_IDLE_COLOR = "#ff00ff"


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
            0, 0, 0, 0,
            swp_nomove | swp_nosize | swp_noactivate | swp_showwindow | swp_framechanged,
        )
    except Exception:
        return


def _set_popup_idle(window) -> None:
    """Keep the popup HWND alive while rendering the validated OBS idle surface."""
    try:
        for child in tuple(window.winfo_children()):
            try:
                child.destroy()
            except Exception:
                pass
        window.configure(background=POPUP_IDLE_COLOR)
        # Keep the beta.6 inactive-surface strategy unchanged until real OBS validation.
        try:
            window.attributes("-transparentcolor", POPUP_IDLE_COLOR)
        except Exception:
            pass
        window.attributes("-alpha", 1.0)
        _set_window_title(window, POPUP_WINDOW_TITLE)
        window.deiconify()
    except Exception:
        pass


def _ensure_obs_popup_window(overlay):
    """Return the single production popup Toplevel owned by this OverlayUI."""
    if not getattr(overlay, "capture_for_obs", False) or getattr(overlay, "_closed", False):
        return None

    window = overlay.toast_window
    if window is not None:
        try:
            if window.winfo_exists():
                return window
        except Exception:
            pass
        overlay._destroy_toast_window()

    window = overlay._create_toast_window()
    window.withdraw()
    _set_window_title(window, POPUP_WINDOW_TITLE)
    window.overrideredirect(True)
    window.attributes("-topmost", True)
    window.configure(background=POPUP_IDLE_COLOR)
    window.geometry(POPUP_IDLE_GEOMETRY)
    window.update_idletasks()
    overlay._apply_window_style(window, click_through=True)
    _clear_toolwindow_style(window)
    _set_popup_idle(window)
    return window


def enable_obs_overlay_capture() -> None:
    """Install instance-local OBS capture hooks for production overlay windows."""
    from dwm import ui_overlays

    style_original = ui_overlays.OverlayUI._apply_window_style
    if not getattr(style_original, "_dwm_obs_capture_wrapper", False):

        def apply_obs_compatible_style(self, window, *, click_through: bool) -> None:
            style_original(self, window, click_through=click_through)
            if self.capture_for_obs:
                _clear_toolwindow_style(window)

        apply_obs_compatible_style._dwm_obs_capture_wrapper = True
        ui_overlays.OverlayUI._apply_window_style = apply_obs_compatible_style

    ensure_original = ui_overlays.OverlayUI._ensure_persistent
    if not getattr(ensure_original, "_dwm_obs_capture_wrapper", False):

        def ensure_obs_persistent(self) -> None:
            ensure_original(self)
            if not self.capture_for_obs:
                return
            window = self.persistent_window
            if window is not None:
                _set_window_title(window, OVERLAY_WINDOW_TITLE)
                _clear_toolwindow_style(window)

        ensure_obs_persistent._dwm_obs_capture_wrapper = True
        ui_overlays.OverlayUI._ensure_persistent = ensure_obs_persistent

    acquire_original = ui_overlays.OverlayUI._acquire_toast_window
    if not getattr(acquire_original, "_dwm_obs_capture_wrapper", False):

        def acquire_obs_focus_popup(self):
            if not self.capture_for_obs:
                return acquire_original(self)
            window = _ensure_obs_popup_window(self)
            if window is None:
                return acquire_original(self)
            for child in tuple(window.winfo_children()):
                try:
                    child.destroy()
                except Exception:
                    pass
            _set_window_title(window, POPUP_WINDOW_TITLE)
            _clear_toolwindow_style(window)
            return window

        acquire_obs_focus_popup._dwm_obs_capture_wrapper = True
        ui_overlays.OverlayUI._acquire_toast_window = acquire_obs_focus_popup

    deactivate_original = ui_overlays.OverlayUI._deactivate_toast_window
    if not getattr(deactivate_original, "_dwm_obs_capture_wrapper", False):

        def deactivate_obs_focus_popup(self) -> None:
            if not self.capture_for_obs:
                deactivate_original(self)
                return
            window = self.toast_window
            if window is None or self._closed:
                return
            try:
                if not window.winfo_exists():
                    self.toast_window = None
                    return
            except Exception:
                self.toast_window = None
                return
            _set_popup_idle(window)
            _clear_toolwindow_style(window)
            self._toast_images.clear()

        deactivate_obs_focus_popup._dwm_obs_capture_wrapper = True
        ui_overlays.OverlayUI._deactivate_toast_window = deactivate_obs_focus_popup

    init_original = ui_overlays.OverlayUI.__init__
    if not getattr(init_original, "_dwm_obs_capture_wrapper", False):

        def init_obs_overlay(self, *args, **kwargs) -> None:
            init_original(self, *args, **kwargs)
            if self.capture_for_obs:
                _ensure_obs_popup_window(self)

        init_obs_overlay._dwm_obs_capture_wrapper = True
        ui_overlays.OverlayUI.__init__ = init_obs_overlay
