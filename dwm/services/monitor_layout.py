from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import os

from .display_overlay import OVERLAY_ANCHORS, place_inside_rect, recover_window_position


@dataclass(frozen=True)
class Monitor:
    identity: str
    area: tuple[int, int, int, int]
    primary: bool = False


def normalize_monitor_anchor(value: object) -> str:
    return value if isinstance(value, str) and value in OVERLAY_ANCHORS else "free"


def list_monitors(root) -> tuple[Monitor, ...]:
    if os.name == "nt":
        class Info(ctypes.Structure):
            _fields_ = [("size", wintypes.DWORD), ("monitor", wintypes.RECT),
                        ("work", wintypes.RECT), ("flags", wintypes.DWORD),
                        ("device", wintypes.WCHAR * 32)]
        try:
            api = ctypes.WinDLL("user32", use_last_error=True)
            callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HANDLE, wintypes.HDC,
                                               ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)
            api.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Info)]
            api.GetMonitorInfoW.restype = wintypes.BOOL
            api.EnumDisplayMonitors.argtypes = [wintypes.HDC, ctypes.POINTER(wintypes.RECT), callback_type, wintypes.LPARAM]
            api.EnumDisplayMonitors.restype = wintypes.BOOL
            monitors = []

            @callback_type
            def collect(handle, _dc, _rect, _data):
                info = Info()
                info.size = ctypes.sizeof(info)
                if api.GetMonitorInfoW(handle, ctypes.byref(info)):
                    rect = info.work
                    if rect.right > rect.left and rect.bottom > rect.top:
                        monitors.append(Monitor(info.device, (rect.left, rect.top, rect.right, rect.bottom), bool(info.flags & 1)))
                return True

            if api.EnumDisplayMonitors(None, None, collect, 0) and monitors:
                return tuple(sorted(monitors, key=lambda monitor: (not monitor.primary, monitor.identity)))
        except (AttributeError, OSError, TypeError):
            pass
    try:
        return (Monitor("primary", (0, 0, int(root.winfo_screenwidth()), int(root.winfo_screenheight())), True),)
    except Exception:
        return ()


def choose_monitor(monitors: tuple[Monitor, ...], identity: str, position: tuple[int, int]) -> Monitor | None:
    if not monitors:
        return None
    if identity:
        return next((monitor for monitor in monitors if monitor.identity == identity),
                    next((monitor for monitor in monitors if monitor.primary), monitors[0]))
    x, y = position
    return min(monitors, key=lambda monitor:
               max(monitor.area[0] - x, 0, x - monitor.area[2]) ** 2
               + max(monitor.area[1] - y, 0, y - monitor.area[3]) ** 2)


def overlay_position(monitors: tuple[Monitor, ...], identity: str, anchor: str,
                     size: tuple[int, int], position: tuple[int, int]) -> tuple[int, int]:
    monitor = choose_monitor(monitors, identity, position)
    if monitor is None:
        return position
    if normalize_monitor_anchor(anchor) != "free":
        return place_inside_rect(monitor.area, size, anchor, margin=16)
    areas = (monitor.area,) if identity else tuple(item.area for item in monitors)
    x, y = recover_window_position(*size, *position, areas)
    if identity:
        left, top, right, bottom = monitor.area
        x = max(left, min(x, max(left, right - size[0])))
        y = max(top, min(y, max(top, bottom - size[1])))
    return x, y
