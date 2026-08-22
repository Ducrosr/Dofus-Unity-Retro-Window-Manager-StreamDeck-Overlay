"""Windows event hook (SetWinEventHook) for near-zero polling.

This module provides WinEventHook: a small helper that listens to
window creation/destruction and title changes.

Important:
- Windows-only.
- The callback must be fast and must not touch Tkinter.
  (Use a Queue to communicate with the UI thread.)
"""

from __future__ import annotations

import threading
from typing import Callable, Iterable, Optional


class WinEventHook:
    """Listen to top-level window events using SetWinEventHook."""

    def __init__(
        self,
        on_event: Callable[[str, int], None],
        class_names: Iterable[str] = ("UnityWndClass", "Chrome_WidgetWin_1"),
        title_keyword_by_class: Optional[dict[str, str]] = None,
    ) -> None:
        self._on_event = on_event
        self._class_names = {str(c) for c in (class_names or []) if str(c)}
        self._title_kw_by_class = {
            str(k): str(v).lower().strip()
            for k, v in (title_keyword_by_class or {}).items()
            if str(k) and str(v).strip()
        }

        self._thread: Optional[threading.Thread] = None
        self._thread_id: int = 0
        self._ready = threading.Event()
        self._stop = threading.Event()

        self._hooks: list[int] = []
        self._cb = None  # keep WinEventProc alive

        self._last_error: Optional[str] = None

    def get_last_error(self) -> Optional[str]:
        return self._last_error

    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self) -> None:
        if self.is_running():
            return
        self._stop.clear()
        self._ready.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        # Wait a bit so thread_id is known (avoid races on stop)
        self._ready.wait(timeout=2.0)

    def stop(self) -> None:
        self._stop.set()
        try:
            self._post_quit()
        except Exception:
            pass
        thread = self._thread
        if thread and thread is not threading.current_thread():
            thread.join(timeout=1.0)
        if thread and not thread.is_alive():
            self._thread = None

    # -------------------- internals --------------------

    def _post_quit(self) -> None:
        import ctypes
        from ctypes import wintypes

        if not self._thread_id:
            return
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        PostThreadMessageW = user32.PostThreadMessageW
        PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        PostThreadMessageW.restype = wintypes.BOOL

        WM_QUIT = 0x0012
        PostThreadMessageW(wintypes.DWORD(self._thread_id), wintypes.UINT(WM_QUIT), wintypes.WPARAM(0), wintypes.LPARAM(0))

    def _run(self) -> None:
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.WinDLL("user32", use_last_error=True)

            # --- constants ---
            EVENT_OBJECT_CREATE = 0x8000
            EVENT_OBJECT_DESTROY = 0x8001
            EVENT_OBJECT_NAMECHANGE = 0x800C

            WINEVENT_OUTOFCONTEXT = 0x0000
            WINEVENT_SKIPOWNPROCESS = 0x0002

            OBJID_WINDOW = 0
            CHILDID_SELF = 0

            # --- WinEventProc ---
            HWINEVENTHOOK = wintypes.HANDLE

            WinEventProcType = ctypes.WINFUNCTYPE(
                None,
                HWINEVENTHOOK,
                wintypes.DWORD,
                wintypes.HWND,
                wintypes.LONG,
                wintypes.LONG,
                wintypes.DWORD,
                wintypes.DWORD,
            )

            # --- APIs ---
            SetWinEventHook = user32.SetWinEventHook
            SetWinEventHook.argtypes = [
                wintypes.DWORD,
                wintypes.DWORD,
                wintypes.HMODULE,
                WinEventProcType,
                wintypes.DWORD,
                wintypes.DWORD,
                wintypes.DWORD,
            ]
            SetWinEventHook.restype = HWINEVENTHOOK

            UnhookWinEvent = user32.UnhookWinEvent
            UnhookWinEvent.argtypes = [HWINEVENTHOOK]
            UnhookWinEvent.restype = wintypes.BOOL

            GetCurrentThreadId = ctypes.WinDLL("kernel32", use_last_error=True).GetCurrentThreadId
            GetCurrentThreadId.argtypes = []
            GetCurrentThreadId.restype = wintypes.DWORD

            GetClassNameW = user32.GetClassNameW
            GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
            GetClassNameW.restype = ctypes.c_int

            GetWindowTextLengthW = user32.GetWindowTextLengthW
            GetWindowTextLengthW.argtypes = [wintypes.HWND]
            GetWindowTextLengthW.restype = ctypes.c_int

            GetWindowTextW = user32.GetWindowTextW
            GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
            GetWindowTextW.restype = ctypes.c_int

            # MSG struct (must match Win32 layout on 64-bit)
            class POINT(ctypes.Structure):
                _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

            class MSG(ctypes.Structure):
                _fields_ = [
                    ("hwnd", wintypes.HWND),
                    ("message", wintypes.UINT),
                    ("wParam", wintypes.WPARAM),
                    ("lParam", wintypes.LPARAM),
                    ("time", wintypes.DWORD),
                    ("pt", POINT),
                    ("lPrivate", wintypes.DWORD),
                ]

            PeekMessageW = user32.PeekMessageW
            PeekMessageW.argtypes = [ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT]
            PeekMessageW.restype = wintypes.BOOL

            GetMessageW = user32.GetMessageW
            GetMessageW.argtypes = [ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
            GetMessageW.restype = wintypes.BOOL

            # Create message queue for this thread (important so WM_QUIT works reliably)
            msg = MSG()
            PM_NOREMOVE = 0x0000
            PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_NOREMOVE)

            self._thread_id = int(GetCurrentThreadId())

            # --- callback ---
            def _event_name(ev: int) -> Optional[str]:
                if ev == EVENT_OBJECT_CREATE:
                    return "create"
                if ev == EVENT_OBJECT_DESTROY:
                    return "destroy"
                if ev == EVENT_OBJECT_NAMECHANGE:
                    return "namechange"
                return None

            @WinEventProcType
            def _cb(hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
                try:
                    if self._stop.is_set():
                        return

                    name = _event_name(int(event))
                    if not name:
                        return

                    if int(idObject) != OBJID_WINDOW or int(idChild) != CHILDID_SELF:
                        return

                    ihwnd = int(hwnd)
                    if ihwnd <= 0:
                        return

                    # Filter by class name to reduce noise.
                    if self._class_names:
                        buf = ctypes.create_unicode_buffer(256)
                        n = GetClassNameW(wintypes.HWND(ihwnd), buf, len(buf))
                        cn = (buf.value or "")[:n]
                        if cn not in self._class_names:
                            return

                        # Optional title keyword filter per class (useful for Retro)
                        kw = self._title_kw_by_class.get(cn, "")
                        if kw:
                            ln = int(GetWindowTextLengthW(wintypes.HWND(ihwnd)))
                            if ln <= 0:
                                ln = 512
                            tbuf = ctypes.create_unicode_buffer(ln + 2)
                            GetWindowTextW(wintypes.HWND(ihwnd), tbuf, len(tbuf))
                            title = (tbuf.value or "").strip().lower()
                            if kw not in title:
                                return

                    # Notify user callback (should be fast, thread-safe).
                    self._on_event(name, ihwnd)
                except Exception:
                    # Never raise from a WinEvent hook callback.
                    return

            self._cb = _cb

            flags = WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS

            # Install one hook per event for clarity.
            self._hooks = []
            for ev in (EVENT_OBJECT_CREATE, EVENT_OBJECT_DESTROY, EVENT_OBJECT_NAMECHANGE):
                h = SetWinEventHook(
                    wintypes.DWORD(ev),
                    wintypes.DWORD(ev),
                    None,
                    _cb,
                    wintypes.DWORD(0),
                    wintypes.DWORD(0),
                    wintypes.DWORD(flags),
                )
                if h:
                    self._hooks.append(int(h))

            if not self._hooks:
                self._last_error = "SetWinEventHook a échoué (aucun hook installé)"

            self._ready.set()

            # Message loop. WM_QUIT will break it.
            while not self._stop.is_set():
                r = GetMessageW(ctypes.byref(msg), None, 0, 0)
                if r == 0:
                    break  # WM_QUIT
                if r == -1:
                    break  # error

        except Exception as e:
            self._last_error = f"WinEventHook error: {e}"
            self._ready.set()
        finally:
            # Unhook if needed
            try:
                import ctypes
                from ctypes import wintypes

                user32 = ctypes.WinDLL("user32", use_last_error=True)
                UnhookWinEvent = user32.UnhookWinEvent
                UnhookWinEvent.argtypes = [wintypes.HANDLE]
                UnhookWinEvent.restype = wintypes.BOOL

                for h in (self._hooks or []):
                    try:
                        UnhookWinEvent(wintypes.HANDLE(h))
                    except Exception:
                        pass
            except Exception:
                pass

            self._hooks = []
            self._thread_id = 0
