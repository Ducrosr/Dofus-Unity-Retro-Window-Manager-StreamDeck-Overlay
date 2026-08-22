"""Fast Win32 window enumeration utilities.

We avoid pywinauto/UIAutomation for scanning windows, which can be slow (and
sometimes requires COM initialisation). For this app, we only need:
- hwnd
- class name
- window title

So we use EnumWindows + GetClassNameW + GetWindowTextW.

Windows-only.
"""

from __future__ import annotations

from typing import List, Optional, Tuple


_last_enum_error = ""


def _make_wndenumproc(ctypes, wintypes):
    """Create the EnumWindows callback type with the Windows calling convention."""
    return ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def _load_win32():
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)

    # BOOL EnumWindows(WNDENUMPROC lpEnumFunc, LPARAM lParam);
    WNDENUMPROC = _make_wndenumproc(ctypes, wintypes)
    EnumWindows = user32.EnumWindows
    EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
    EnumWindows.restype = wintypes.BOOL

    GetClassNameW = user32.GetClassNameW
    GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    GetClassNameW.restype = ctypes.c_int

    GetWindowTextLengthW = user32.GetWindowTextLengthW
    GetWindowTextLengthW.argtypes = [wintypes.HWND]
    GetWindowTextLengthW.restype = ctypes.c_int

    GetWindowTextW = user32.GetWindowTextW
    GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    GetWindowTextW.restype = ctypes.c_int

    IsWindowVisible = user32.IsWindowVisible
    IsWindowVisible.argtypes = [wintypes.HWND]
    IsWindowVisible.restype = wintypes.BOOL

    IsWindow = user32.IsWindow
    IsWindow.argtypes = [wintypes.HWND]
    IsWindow.restype = wintypes.BOOL

    return (
        ctypes,
        wintypes,
        WNDENUMPROC,
        EnumWindows,
        GetClassNameW,
        GetWindowTextLengthW,
        GetWindowTextW,
        IsWindowVisible,
        IsWindow,
    )


def get_class_name(hwnd: int) -> str:
    try:
        ctypes, wintypes, _, _, GetClassNameW, *_rest = _load_win32()
        buf = ctypes.create_unicode_buffer(256)
        n = GetClassNameW(wintypes.HWND(hwnd), buf, len(buf))
        return (buf.value or "")[:n]
    except Exception:
        return ""


def get_window_title(hwnd: int) -> str:
    try:
        ctypes, wintypes, _, _, _, GetWindowTextLengthW, GetWindowTextW, *_rest = _load_win32()
        length = int(GetWindowTextLengthW(wintypes.HWND(hwnd)))
        if length <= 0:
            # Still try a small buffer (some windows return 0 but have text)
            length = 512
        buf = ctypes.create_unicode_buffer(length + 2)
        GetWindowTextW(wintypes.HWND(hwnd), buf, len(buf))
        return (buf.value or "").strip()
    except Exception:
        return ""


def enum_top_level_windows(
    class_name: Optional[str] = None,
    visible_only: bool = True,
) -> List[Tuple[int, str]]:
    """Return list of (hwnd, title) for top-level windows matching class_name.

    - If class_name is None, returns all windows.
    - If visible_only is True, keeps only visible windows.
    """
    global _last_enum_error

    try:
        (
            ctypes,
            _wintypes,
            WNDENUMPROC,
            EnumWindows,
            GetClassNameW,
            GetWindowTextLengthW,
            GetWindowTextW,
            IsWindowVisible,
            IsWindow,
        ) = _load_win32()

        wanted = class_name
        if wanted is not None:
            wanted = str(wanted)

        results: List[Tuple[int, str]] = []

        @WNDENUMPROC
        def _cb(hwnd, lparam):
            try:
                if not IsWindow(hwnd):
                    return True
                if visible_only and not IsWindowVisible(hwnd):
                    return True

                if wanted:
                    buf = ctypes.create_unicode_buffer(256)
                    n = GetClassNameW(hwnd, buf, len(buf))
                    cn = (buf.value or "")[:n]
                    if cn != wanted:
                        return True

                # title
                length = int(GetWindowTextLengthW(hwnd))
                if length <= 0:
                    # Some windows report 0 even with text; try anyway.
                    length = 512
                tbuf = ctypes.create_unicode_buffer(length + 2)
                GetWindowTextW(hwnd, tbuf, len(tbuf))
                title = (tbuf.value or "").strip()
                if not title:
                    return True

                results.append((int(hwnd), title))
                return True
            except Exception:
                return True

        if not EnumWindows(_cb, 0):
            raise OSError("EnumWindows a retourné False")
        _last_enum_error = ""
        return results
    except Exception as exc:
        _last_enum_error = f"{type(exc).__name__}: {exc}"
        return []


def get_last_enum_error() -> str:
    return _last_enum_error
