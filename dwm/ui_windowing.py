from __future__ import annotations

import ctypes
import os

from .services.monitor_layout import choose_monitor, list_monitors


WINDOW_MARGIN = 24


def centered_position(
    parent_x: int,
    parent_y: int,
    parent_width: int,
    parent_height: int,
    child_width: int,
    child_height: int,
) -> tuple[int, int]:
    return (
        int(parent_x + (parent_width - child_width) / 2),
        int(parent_y + (parent_height - child_height) / 2),
    )


def _widget_is_visible(widget) -> bool:
    try:
        state = str(widget.state())
        if state in {"withdrawn", "iconic"}:
            return False
    except Exception:
        pass
    try:
        return bool(widget.winfo_viewable())
    except Exception:
        return False


def _monitor_for_window(window, parent=None):
    monitors = list_monitors(window)
    if not monitors:
        return None

    if parent is not None and _widget_is_visible(parent):
        try:
            parent.update_idletasks()
            point = (
                int(parent.winfo_rootx()) + max(1, int(parent.winfo_width())) // 2,
                int(parent.winfo_rooty()) + max(1, int(parent.winfo_height())) // 2,
            )
            return choose_monitor(monitors, "", point)
        except Exception:
            pass

    try:
        point = (
            int(window.winfo_pointerx()),
            int(window.winfo_pointery()),
        )
        return choose_monitor(monitors, "", point)
    except Exception:
        return next((item for item in monitors if item.primary), monitors[0])


def _clamp_geometry_to_work_area(
    x: int,
    y: int,
    width: int,
    height: int,
    area: tuple[int, int, int, int],
    *,
    margin: int = WINDOW_MARGIN,
) -> tuple[int, int, int, int]:
    left, top, right, bottom = area
    usable_width = max(1, right - left - (margin * 2))
    usable_height = max(1, bottom - top - (margin * 2))
    width = min(max(1, width), usable_width)
    height = min(max(1, height), usable_height)
    min_x = left + margin
    min_y = top + margin
    max_x = max(min_x, right - margin - width)
    max_y = max(min_y, bottom - margin - height)
    return (
        max(min_x, min(int(x), max_x)),
        max(min_y, min(int(y), max_y)),
        width,
        height,
    )


def apply_windows_dark_titlebar(window) -> None:
    """Ask Windows 10/11 to render the native caption using dark chrome."""
    if os.name != "nt":
        return
    try:
        window.update_idletasks()
        hwnd = int(window.winfo_id())
        dwmapi = ctypes.WinDLL("dwmapi", use_last_error=True)
        value = ctypes.c_int(1)
        for attribute in (20, 19):  # current + older immersive dark-mode ids
            result = dwmapi.DwmSetWindowAttribute(
                ctypes.c_void_p(hwnd),
                ctypes.c_uint(attribute),
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
            if result == 0:
                break
    except Exception:
        return


def center_window_on_parent(window, parent=None) -> None:
    """Center a dialog and keep it fully inside the current monitor work area.

    Overlay, popup and compact windows deliberately do not use this helper
    because their desktop position is part of their functionality.
    """
    try:
        window.update_idletasks()
        child_width = max(int(window.winfo_width()), int(window.winfo_reqwidth()))
        child_height = max(int(window.winfo_height()), int(window.winfo_reqheight()))

        if parent is not None and _widget_is_visible(parent):
            parent.update_idletasks()
            x, y = centered_position(
                int(parent.winfo_rootx()),
                int(parent.winfo_rooty()),
                max(1, int(parent.winfo_width())),
                max(1, int(parent.winfo_height())),
                child_width,
                child_height,
            )
        else:
            x, y = centered_position(
                0,
                0,
                int(window.winfo_screenwidth()),
                int(window.winfo_screenheight()),
                child_width,
                child_height,
            )

        monitor = _monitor_for_window(window, parent)
        if monitor is not None:
            x, y, child_width, child_height = _clamp_geometry_to_work_area(
                x,
                y,
                child_width,
                child_height,
                monitor.area,
            )
            window.geometry(f"{child_width}x{child_height}+{x}+{y}")
        else:
            window.geometry(f"+{x}+{y}")
        apply_windows_dark_titlebar(window)
    except Exception:
        return


def schedule_center_window(window, parent=None) -> None:
    """Center/clamp after Tk has computed the dialog's requested dimensions."""
    try:
        window.after_idle(lambda: center_window_on_parent(window, parent))
    except Exception:
        center_window_on_parent(window, parent)


def install_combobox_wheel_guard(root) -> None:
    """Prevent accidental value changes on closed choice/numeric controls.

    ttk Combobox and ttk Spinbox both react to the mouse wheel by default.
    Replacing their class bindings removes that value-changing behavior while
    returning None so the event can continue to the containing window/canvas.
    This keeps normal page scrolling intact.

    An opened Combobox drop-down uses its own listbox, so the list itself
    remains scrollable.
    """

    def ignore_value_change(_event):
        return None

    for widget_class in ("TCombobox", "TSpinbox"):
        try:
            root.bind_class(widget_class, "<MouseWheel>", ignore_value_change)
        except Exception:
            pass
        # Kept for completeness on Tk builds that report wheel events this way.
        for sequence in ("<Button-4>", "<Button-5>"):
            try:
                root.bind_class(widget_class, sequence, ignore_value_change)
            except Exception:
                pass
