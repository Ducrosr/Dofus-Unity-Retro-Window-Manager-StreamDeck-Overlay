"""Best-effort Windows shell listener for taskbar attention flashes.

RegisterShellHookWindow is intentionally isolated here because Microsoft marks
it as a Shell-oriented API that can be unavailable on a future Windows build.
The regular EVENT_SYSTEM_ALERT hook remains active as a fallback.
"""

from __future__ import annotations

import os
import threading
from collections.abc import Callable


HSHELL_WINDOWACTIVATED = 4
HSHELL_FLASH = 0x8006
HSHELL_RUDEAPPACTIVATED = 0x8004


def classify_shell_event(code: int) -> str | None:
    normalized = int(code)
    if normalized == HSHELL_FLASH:
        return "attention"
    if normalized in {HSHELL_WINDOWACTIVATED, HSHELL_RUDEAPPACTIVATED}:
        return "foreground"
    return None


class ShellAttentionHook:
    def __init__(self, on_event: Callable[[str, int], None]) -> None:
        self._on_event = on_event
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._stop = threading.Event()
        self._hwnd = 0
        self._thread_id = 0
        self._wndproc = None
        self._last_error: str | None = None

    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive() and self._hwnd)

    def get_last_error(self) -> str | None:
        return self._last_error

    def start(self) -> None:
        if self.is_running():
            return
        if os.name != "nt":
            self._last_error = "La détection d’attention Shell nécessite Windows."
            return
        self._stop.clear()
        self._ready.clear()
        self._thread = threading.Thread(target=self._run, name="DWMShellAttention", daemon=True)
        self._thread.start()
        self._ready.wait(timeout=2.0)

    def stop(self) -> None:
        self._stop.set()
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.WinDLL("user32", use_last_error=True)
            if self._hwnd:
                user32.PostMessageW(wintypes.HWND(self._hwnd), 0x0010, 0, 0)  # WM_CLOSE
            elif self._thread_id:
                user32.PostThreadMessageW(wintypes.DWORD(self._thread_id), 0x0012, 0, 0)  # WM_QUIT
        except Exception:
            pass
        thread = self._thread
        if thread and thread is not threading.current_thread():
            thread.join(timeout=1.5)
        if thread and not thread.is_alive():
            self._thread = None

    def _run(self) -> None:
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.WinDLL("user32", use_last_error=True)
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            lresult = ctypes.c_ssize_t
            WndProcType = ctypes.WINFUNCTYPE(lresult, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

            class WNDCLASSW(ctypes.Structure):
                _fields_ = (
                    ("style", wintypes.UINT),
                    ("lpfnWndProc", WndProcType),
                    ("cbClsExtra", ctypes.c_int),
                    ("cbWndExtra", ctypes.c_int),
                    ("hInstance", wintypes.HINSTANCE),
                    ("hIcon", wintypes.HANDLE),
                    ("hCursor", wintypes.HANDLE),
                    ("hbrBackground", wintypes.HANDLE),
                    ("lpszMenuName", wintypes.LPCWSTR),
                    ("lpszClassName", wintypes.LPCWSTR),
                )

            class POINT(ctypes.Structure):
                _fields_ = (("x", wintypes.LONG), ("y", wintypes.LONG))

            class MSG(ctypes.Structure):
                _fields_ = (
                    ("hwnd", wintypes.HWND),
                    ("message", wintypes.UINT),
                    ("wParam", wintypes.WPARAM),
                    ("lParam", wintypes.LPARAM),
                    ("time", wintypes.DWORD),
                    ("pt", POINT),
                    ("lPrivate", wintypes.DWORD),
                )

            DefWindowProcW = user32.DefWindowProcW
            DefWindowProcW.argtypes = (wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
            DefWindowProcW.restype = lresult
            DestroyWindow = user32.DestroyWindow
            DestroyWindow.argtypes = (wintypes.HWND,)
            DestroyWindow.restype = wintypes.BOOL
            PostQuitMessage = user32.PostQuitMessage
            PostQuitMessage.argtypes = (ctypes.c_int,)
            RegisterWindowMessageW = user32.RegisterWindowMessageW
            RegisterWindowMessageW.argtypes = (wintypes.LPCWSTR,)
            RegisterWindowMessageW.restype = wintypes.UINT
            RegisterShellHookWindow = user32.RegisterShellHookWindow
            RegisterShellHookWindow.argtypes = (wintypes.HWND,)
            RegisterShellHookWindow.restype = wintypes.BOOL
            DeregisterShellHookWindow = user32.DeregisterShellHookWindow
            DeregisterShellHookWindow.argtypes = (wintypes.HWND,)
            DeregisterShellHookWindow.restype = wintypes.BOOL
            RegisterClassW = user32.RegisterClassW
            RegisterClassW.argtypes = (ctypes.POINTER(WNDCLASSW),)
            RegisterClassW.restype = wintypes.ATOM
            CreateWindowExW = user32.CreateWindowExW
            CreateWindowExW.argtypes = (
                wintypes.DWORD,
                wintypes.LPCWSTR,
                wintypes.LPCWSTR,
                wintypes.DWORD,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                wintypes.HWND,
                wintypes.HMENU,
                wintypes.HINSTANCE,
                wintypes.LPVOID,
            )
            CreateWindowExW.restype = wintypes.HWND
            GetMessageW = user32.GetMessageW
            GetMessageW.argtypes = (ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT)
            GetMessageW.restype = ctypes.c_int
            TranslateMessage = user32.TranslateMessage
            TranslateMessage.argtypes = (ctypes.POINTER(MSG),)
            TranslateMessage.restype = wintypes.BOOL
            DispatchMessageW = user32.DispatchMessageW
            DispatchMessageW.argtypes = (ctypes.POINTER(MSG),)
            DispatchMessageW.restype = lresult
            IsWindow = user32.IsWindow
            IsWindow.argtypes = (wintypes.HWND,)
            IsWindow.restype = wintypes.BOOL
            UnregisterClassW = user32.UnregisterClassW
            UnregisterClassW.argtypes = (wintypes.LPCWSTR, wintypes.HINSTANCE)
            UnregisterClassW.restype = wintypes.BOOL
            GetModuleHandleW = kernel32.GetModuleHandleW
            GetModuleHandleW.argtypes = (wintypes.LPCWSTR,)
            GetModuleHandleW.restype = wintypes.HMODULE
            GetCurrentThreadId = kernel32.GetCurrentThreadId
            GetCurrentThreadId.argtypes = ()
            GetCurrentThreadId.restype = wintypes.DWORD

            shell_message = int(RegisterWindowMessageW("SHELLHOOK"))
            if not shell_message:
                raise OSError("RegisterWindowMessageW(SHELLHOOK) a échoué")

            @WndProcType
            def wndproc(hwnd, message, wparam, lparam):
                try:
                    if int(message) == shell_message:
                        event = classify_shell_event(int(wparam))
                        target = int(lparam)
                        if event and target > 0 and not self._stop.is_set():
                            self._on_event(event, target)
                        return 0
                    if int(message) == 0x0010:  # WM_CLOSE
                        DestroyWindow(hwnd)
                        return 0
                    if int(message) == 0x0002:  # WM_DESTROY
                        PostQuitMessage(0)
                        return 0
                except Exception:
                    return 0
                return DefWindowProcW(hwnd, message, wparam, lparam)

            self._wndproc = wndproc
            hinstance = GetModuleHandleW(None)
            class_name = f"DwmAttentionHook_{os.getpid()}_{id(self)}"
            window_class = WNDCLASSW(
                0,
                wndproc,
                0,
                0,
                hinstance,
                None,
                None,
                None,
                None,
                class_name,
            )
            atom = RegisterClassW(ctypes.byref(window_class))
            if not atom:
                raise OSError("RegisterClassW a échoué")

            hwnd = CreateWindowExW(
                0,
                class_name,
                "DWM attention listener",
                0,
                0,
                0,
                0,
                0,
                None,
                None,
                hinstance,
                None,
            )
            if not hwnd:
                raise OSError("CreateWindowExW a échoué")
            self._hwnd = int(hwnd)
            self._thread_id = int(GetCurrentThreadId())
            if not RegisterShellHookWindow(wintypes.HWND(hwnd)):
                raise OSError("RegisterShellHookWindow a échoué")
            self._ready.set()

            msg = MSG()
            while not self._stop.is_set():
                result = GetMessageW(ctypes.byref(msg), None, 0, 0)
                if result <= 0:
                    break
                TranslateMessage(ctypes.byref(msg))
                DispatchMessageW(ctypes.byref(msg))

            try:
                DeregisterShellHookWindow(wintypes.HWND(hwnd))
            except Exception:
                pass
            try:
                if IsWindow(wintypes.HWND(hwnd)):
                    DestroyWindow(wintypes.HWND(hwnd))
            except Exception:
                pass
            try:
                UnregisterClassW(class_name, hinstance)
            except Exception:
                pass
        except Exception as exc:
            self._last_error = f"ShellAttentionHook: {exc}"
            self._ready.set()
        finally:
            self._hwnd = 0
            self._thread_id = 0
            self._wndproc = None
