from __future__ import annotations

import ctypes
import ntpath
import os
import time
from ctypes import wintypes
from dataclasses import dataclass
from typing import Protocol


SW_RESTORE = 9
SW_MAXIMIZE = 3
SW_FORCEMINIMIZE = 11
WPF_RESTORETOMAXIMIZED = 0x0002
VK_MENU = 0x12
KEYEVENTF_KEYUP = 0x0002
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
WM_SYSCOMMAND = 0x0112
SC_MINIMIZE = 0xF020
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [
        ("length", wintypes.UINT),
        ("flags", wintypes.UINT),
        ("showCmd", wintypes.UINT),
        ("ptMinPosition", POINT),
        ("ptMaxPosition", POINT),
        ("rcNormalPosition", RECT),
    ]


class FocusError(RuntimeError):
    pass


@dataclass(frozen=True)
class _ReleaseResult:
    focused: bool
    diagnostic: str


class _FocusApi(Protocol):
    def is_window(self, hwnd: int) -> bool: ...

    def is_iconic(self, hwnd: int) -> bool: ...

    def should_restore_to_maximized(self, hwnd: int) -> bool: ...

    def show_window(self, hwnd: int, command: int) -> None: ...

    def get_foreground_window(self) -> int: ...

    def get_window_thread_id(self, hwnd: int) -> int: ...

    def get_current_thread_id(self) -> int: ...

    def attach_thread_input(self, source_thread: int, target_thread: int, attach: bool) -> bool: ...

    def bring_window_to_top(self, hwnd: int) -> None: ...

    def set_foreground_window(self, hwnd: int) -> bool: ...

    def set_active_window(self, hwnd: int) -> None: ...

    def set_focus(self, hwnd: int) -> None: ...

    def switch_to_window(self, hwnd: int) -> None: ...

    def tap_alt(self) -> None: ...

    def get_window_process_name(self, hwnd: int) -> str: ...

    def get_window_title(self, hwnd: int) -> str: ...

    def prepare_window_for_activation(self, hwnd: int) -> bool: ...

    def minimize_window_async(self, hwnd: int) -> bool: ...

    def post_minimize_command(self, hwnd: int) -> bool: ...

    def force_minimize_window(self, hwnd: int) -> None: ...

    def pulse_topmost(self, hwnd: int) -> None: ...


class _Win32FocusApi:
    def __init__(self) -> None:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.user32 = user32
        self.kernel32 = kernel32

        user32.GetForegroundWindow.argtypes = []
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
        user32.AttachThreadInput.restype = wintypes.BOOL
        user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.ShowWindow.restype = wintypes.BOOL
        user32.ShowWindowAsync.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.ShowWindowAsync.restype = wintypes.BOOL
        user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.PostMessageW.restype = wintypes.BOOL
        user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        user32.GetWindowTextLengthW.restype = ctypes.c_int
        user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user32.GetWindowTextW.restype = ctypes.c_int
        user32.SetWindowPos.argtypes = [
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        ]
        user32.SetWindowPos.restype = wintypes.BOOL
        user32.BringWindowToTop.argtypes = [wintypes.HWND]
        user32.BringWindowToTop.restype = wintypes.BOOL
        user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        user32.SetForegroundWindow.restype = wintypes.BOOL
        user32.SetActiveWindow.argtypes = [wintypes.HWND]
        user32.SetActiveWindow.restype = wintypes.HWND
        user32.SetFocus.argtypes = [wintypes.HWND]
        user32.SetFocus.restype = wintypes.HWND
        user32.SwitchToThisWindow.argtypes = [wintypes.HWND, wintypes.BOOL]
        user32.SwitchToThisWindow.restype = None
        user32.IsIconic.argtypes = [wintypes.HWND]
        user32.IsIconic.restype = wintypes.BOOL
        user32.IsWindow.argtypes = [wintypes.HWND]
        user32.IsWindow.restype = wintypes.BOOL
        user32.GetWindowPlacement.argtypes = [wintypes.HWND, ctypes.POINTER(WINDOWPLACEMENT)]
        user32.GetWindowPlacement.restype = wintypes.BOOL
        user32.keybd_event.argtypes = [wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ctypes.c_void_p]
        user32.keybd_event.restype = None
        kernel32.GetCurrentThreadId.argtypes = []
        kernel32.GetCurrentThreadId.restype = wintypes.DWORD
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

    @staticmethod
    def _handle(hwnd: int) -> wintypes.HWND:
        return wintypes.HWND(hwnd)

    def is_window(self, hwnd: int) -> bool:
        return bool(self.user32.IsWindow(self._handle(hwnd)))

    def is_iconic(self, hwnd: int) -> bool:
        return bool(self.user32.IsIconic(self._handle(hwnd)))

    def should_restore_to_maximized(self, hwnd: int) -> bool:
        placement = WINDOWPLACEMENT()
        placement.length = ctypes.sizeof(WINDOWPLACEMENT)
        if not self.user32.GetWindowPlacement(self._handle(hwnd), ctypes.byref(placement)):
            return False
        return bool(placement.flags & WPF_RESTORETOMAXIMIZED)

    def show_window(self, hwnd: int, command: int) -> None:
        self.user32.ShowWindow(self._handle(hwnd), command)

    def get_foreground_window(self) -> int:
        return int(self.user32.GetForegroundWindow() or 0)

    def get_window_thread_id(self, hwnd: int) -> int:
        return int(self.user32.GetWindowThreadProcessId(self._handle(hwnd), None))

    def get_current_thread_id(self) -> int:
        return int(self.kernel32.GetCurrentThreadId())

    def attach_thread_input(self, source_thread: int, target_thread: int, attach: bool) -> bool:
        return bool(self.user32.AttachThreadInput(source_thread, target_thread, attach))

    def bring_window_to_top(self, hwnd: int) -> None:
        self.user32.BringWindowToTop(self._handle(hwnd))

    def set_foreground_window(self, hwnd: int) -> bool:
        return bool(self.user32.SetForegroundWindow(self._handle(hwnd)))

    def set_active_window(self, hwnd: int) -> None:
        self.user32.SetActiveWindow(self._handle(hwnd))

    def set_focus(self, hwnd: int) -> None:
        self.user32.SetFocus(self._handle(hwnd))

    def switch_to_window(self, hwnd: int) -> None:
        self.user32.SwitchToThisWindow(self._handle(hwnd), True)

    def tap_alt(self) -> None:
        self.user32.keybd_event(VK_MENU, 0, 0, None)
        self.user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, None)

    def get_window_process_name(self, hwnd: int) -> str:
        process_id = wintypes.DWORD()
        self.user32.GetWindowThreadProcessId(self._handle(hwnd), ctypes.byref(process_id))
        if not process_id.value:
            return ""

        process = self.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, process_id.value)
        if not process:
            return ""
        try:
            buffer = ctypes.create_unicode_buffer(32768)
            size = wintypes.DWORD(len(buffer))
            if not self.kernel32.QueryFullProcessImageNameW(process, 0, buffer, ctypes.byref(size)):
                return ""
            return ntpath.basename(buffer.value)
        finally:
            self.kernel32.CloseHandle(process)

    def get_window_title(self, hwnd: int) -> str:
        handle = self._handle(hwnd)
        length = max(0, int(self.user32.GetWindowTextLengthW(handle)))
        buffer = ctypes.create_unicode_buffer(max(2, length + 1))
        self.user32.GetWindowTextW(handle, buffer, len(buffer))
        return buffer.value.strip()

    def prepare_window_for_activation(self, hwnd: int) -> bool:
        flags = SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
        return bool(self.user32.SetWindowPos(self._handle(hwnd), wintypes.HWND(0), 0, 0, 0, 0, flags))

    def minimize_window_async(self, hwnd: int) -> bool:
        return bool(self.user32.ShowWindowAsync(self._handle(hwnd), SW_FORCEMINIMIZE))

    def post_minimize_command(self, hwnd: int) -> bool:
        return bool(
            self.user32.PostMessageW(
                self._handle(hwnd),
                WM_SYSCOMMAND,
                wintypes.WPARAM(SC_MINIMIZE),
                wintypes.LPARAM(0),
            )
        )

    def force_minimize_window(self, hwnd: int) -> None:
        self.user32.ShowWindow(self._handle(hwnd), SW_FORCEMINIMIZE)

    def pulse_topmost(self, hwnd: int) -> None:
        flags = SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
        handle = self._handle(hwnd)
        self.user32.SetWindowPos(handle, wintypes.HWND(-1), 0, 0, 0, 0, flags)
        self.user32.SetWindowPos(handle, wintypes.HWND(-2), 0, 0, 0, 0, flags)


_WINDOWS_API: _Win32FocusApi | None = _Win32FocusApi() if os.name == "nt" else None


def is_window(hwnd: int) -> bool:
    """Return True if hwnd is a valid window handle."""
    api = _WINDOWS_API
    if api is None:
        return False
    try:
        return api.is_window(int(hwnd))
    except Exception:
        return False


def get_foreground_hwnd() -> int:
    """Return the current foreground window handle, or 0 when unavailable."""
    api = _WINDOWS_API
    if api is None:
        return 0
    try:
        return api.get_foreground_window()
    except Exception:
        return 0


def focus_hwnd(hwnd: int) -> None:
    """Restore and reliably activate a top-level window by handle."""
    api = _WINDOWS_API
    if api is None:
        raise FocusError("Le changement de fenêtre est disponible uniquement sous Windows.")
    _focus_hwnd_with_api(int(hwnd), api)


def _focus_hwnd_with_api(hwnd: int, api: _FocusApi, *, verify_timeout: float = 0.18) -> None:
    if not hwnd or not api.is_window(hwnd):
        raise FocusError("handle de fenêtre invalide")

    _restore_minimized_window(hwnd, api)
    if _wait_for_foreground(hwnd, api, 0):
        return
    try:
        if api.set_foreground_window(hwnd) and _wait_for_foreground(hwnd, api, verify_timeout):
            api.bring_window_to_top(hwnd)
            return
    except Exception:
        pass

    try:
        foreground = api.get_foreground_window()
        current_thread = api.get_current_thread_id()
        foreground_thread = api.get_window_thread_id(foreground) if foreground else 0
        target_thread = api.get_window_thread_id(hwnd)
    except Exception:
        foreground_thread = 0
        target_thread = 0
        current_thread = 0
    attached_threads: list[int] = []

    # Joining both the foreground process (Stream Deck in the reported case)
    # and the Dofus target to our UI thread gives SetActiveWindow/SetFocus a
    # shared input queue. Attaching only to the foreground thread is not enough.
    for thread_id in (foreground_thread, target_thread):
        if not thread_id or thread_id == current_thread or thread_id in attached_threads:
            continue
        try:
            if api.attach_thread_input(current_thread, thread_id, True):
                attached_threads.append(thread_id)
        except Exception:
            continue

    try:
        api.bring_window_to_top(hwnd)
        api.set_foreground_window(hwnd)
        api.set_active_window(hwnd)
        api.set_focus(hwnd)
    except Exception:
        pass
    finally:
        for thread_id in reversed(attached_threads):
            try:
                api.attach_thread_input(current_thread, thread_id, False)
            except Exception:
                pass

    if _wait_for_foreground(hwnd, api, verify_timeout):
        return

    # SwitchToThisWindow is retained as a compatibility fallback for Unity
    # windows that reject the documented activation sequence.
    try:
        api.switch_to_window(hwnd)
    except Exception:
        pass
    if _wait_for_foreground(hwnd, api, verify_timeout):
        return

    # A short, balanced Alt press clears Windows' foreground lock without
    # sending a character to the game. This fallback is only reached after the
    # regular activation methods have failed.
    try:
        api.tap_alt()
        api.bring_window_to_top(hwnd)
        api.set_foreground_window(hwnd)
    except Exception:
        pass
    if _wait_for_foreground(hwnd, api, verify_timeout):
        return

    # Stream Deck's desktop UI is a special case: the hardware press reaches
    # the plugin through IPC, so this manager is not the process that received
    # the last Windows input event. If Stream Deck itself still owns the
    # foreground, put Dofus directly behind it in the Z order, then minimize
    # only Stream Deck. SW_MINIMIZE activates the next top-level window, which
    # is now the requested Dofus client. No unrelated foreground app is touched.
    release = _release_streamdeck_foreground(hwnd, api, verify_timeout=max(0.28, verify_timeout))
    if release.focused:
        return

    raise FocusError(release.diagnostic or "Windows a bloqué la mise au premier plan")


def _release_streamdeck_foreground(hwnd: int, api: _FocusApi, verify_timeout: float) -> _ReleaseResult:
    process_name = ""
    window_title = ""
    try:
        foreground = api.get_foreground_window()
        if not foreground or foreground == hwnd:
            return _ReleaseResult(foreground == hwnd, "Windows n’indique aucune fenêtre bloquante.")
        process_name = api.get_window_process_name(foreground)
        window_title = api.get_window_title(foreground)
        if not _is_streamdeck_window(process_name, window_title):
            blocker = _format_blocker(process_name, window_title)
            return _ReleaseResult(False, f"Windows a conservé une autre fenêtre au premier plan ({blocker}).")
    except Exception as exc:
        return _ReleaseResult(False, f"Impossible d’identifier la fenêtre au premier plan ({exc}).")

    # Preparing the Z order improves the usual path, but it must not prevent
    # the minimization fallback when Windows refuses SetWindowPos.
    prepared = False
    try:
        prepared = api.prepare_window_for_activation(hwnd)
    except Exception:
        pass

    released, attempts = _force_release_foreground_window(foreground, api, timeout=0.42)
    blocker = _format_blocker(process_name, window_title)
    details = ", ".join(attempts) or "aucune méthode disponible"
    if not released:
        prep = "préparation Z réussie" if prepared else "préparation Z refusée"
        return _ReleaseResult(
            False,
            f"Stream Deck détecté mais sa réduction a été bloquée ({blocker}; {prep}; {details}).",
        )

    if _wait_for_foreground(hwnd, api, verify_timeout):
        return _ReleaseResult(True, "")

    # Stream Deck is no longer blocking. Promote the target once, then retry
    # all activation calls while no input queue owned by Stream Deck is active.
    try:
        api.pulse_topmost(hwnd)
        api.bring_window_to_top(hwnd)
        api.set_foreground_window(hwnd)
        api.set_active_window(hwnd)
        api.set_focus(hwnd)
        api.switch_to_window(hwnd)
    except Exception:
        pass
    if _wait_for_foreground(hwnd, api, verify_timeout):
        return _ReleaseResult(True, "")
    return _ReleaseResult(
        False,
        f"Stream Deck a été réduit, mais Windows n’a pas activé la fenêtre Dofus ({blocker}; {details}).",
    )


def _force_release_foreground_window(
    foreground: int,
    api: _FocusApi,
    *,
    timeout: float,
) -> tuple[bool, tuple[str, ...]]:
    attempts: list[str] = []
    methods = (
        ("ShowWindowAsync/SW_FORCEMINIMIZE", api.minimize_window_async),
        ("WM_SYSCOMMAND/SC_MINIMIZE", api.post_minimize_command),
        ("ShowWindow/SW_FORCEMINIMIZE", api.force_minimize_window),
    )
    per_attempt_timeout = max(0.04, timeout / len(methods))

    for name, method in methods:
        try:
            result = method(foreground)
            if result is False:
                attempts.append(f"{name}=refusé")
            else:
                attempts.append(f"{name}=envoyé")
        except Exception as exc:
            attempts.append(f"{name}=erreur {type(exc).__name__}")
        if _wait_for_window_release(foreground, api, per_attempt_timeout):
            return True, tuple(attempts)
    return False, tuple(attempts)


def _wait_for_window_release(foreground: int, api: _FocusApi, timeout: float) -> bool:
    deadline = time.monotonic() + max(0.0, timeout)
    while True:
        try:
            if api.is_iconic(foreground) or api.get_foreground_window() != foreground:
                return True
        except Exception:
            return False
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.01)


def _is_streamdeck_window(process_name: str, window_title: str) -> bool:
    title = str(window_title or "").strip().casefold()
    return _is_streamdeck_process_name(process_name) or title == "stream deck" or title.startswith("stream deck ")


def _is_streamdeck_process_name(process_name: str) -> bool:
    executable = ntpath.basename(str(process_name or "")).strip().lower()
    normalized = executable.replace(" ", "").replace("-", "")
    return normalized in {"streamdeck", "streamdeck.exe", "elgatostreamdeck", "elgatostreamdeck.exe"}


def _format_blocker(process_name: str, window_title: str) -> str:
    process = str(process_name or "processus inconnu").strip()
    title = str(window_title or "titre inconnu").strip().replace("\r", " ").replace("\n", " ")
    if len(title) > 80:
        title = f"{title[:77]}…"
    return f"processus={process}, titre={title}"


def _restore_minimized_window(hwnd: int, api: _FocusApi) -> None:
    try:
        if not api.is_iconic(hwnd):
            return
        restore_to_maximized = api.should_restore_to_maximized(hwnd)
        api.show_window(hwnd, SW_RESTORE)
        if restore_to_maximized:
            api.show_window(hwnd, SW_MAXIMIZE)
    except Exception:
        pass


def _wait_for_foreground(hwnd: int, api: _FocusApi, timeout: float) -> bool:
    deadline = time.monotonic() + max(0.0, timeout)
    while True:
        try:
            if api.get_foreground_window() == hwnd:
                return True
        except Exception:
            return False
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.01)
