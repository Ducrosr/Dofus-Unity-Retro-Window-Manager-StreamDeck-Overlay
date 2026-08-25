from __future__ import annotations

import os

if os.name != "nt":
    raise RuntimeError("Ce module fonctionne uniquement sous Windows.")


import ctypes
import threading
from ctypes import wintypes
from typing import Callable, Dict, Optional, Tuple

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012

WM_APP = 0x8000
WM_HK_REGISTER = WM_APP + 1
WM_HK_UNREGISTER = WM_APP + 2

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

# Virtual key codes
VK_F1 = 0x70

_SPECIAL_VK = {
    "tab": 0x09,
    "enter": 0x0D,
    "return": 0x0D,
    "esc": 0x1B,
    "escape": 0x1B,
    "space": 0x20,
    "backspace": 0x08,
    "delete": 0x2E,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pagedown": 0x22,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
}


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
        ("lPrivate", wintypes.DWORD),
    ]


# --- Win32 prototypes (avoid ABI issues on 64-bit) ---
user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
user32.RegisterHotKey.restype = wintypes.BOOL

user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
user32.UnregisterHotKey.restype = wintypes.BOOL

user32.GetMessageW.argtypes = [ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = ctypes.c_int

user32.PeekMessageW.argtypes = [ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT]
user32.PeekMessageW.restype = wintypes.BOOL

user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostThreadMessageW.restype = wintypes.BOOL

kernel32.GetCurrentThreadId.argtypes = []
kernel32.GetCurrentThreadId.restype = wintypes.DWORD

PM_NOREMOVE = 0x0000


def _vk_from_key(key: str) -> Optional[int]:
    k = key.strip().lower()
    if not k:
        return None

    if k in _SPECIAL_VK:
        return _SPECIAL_VK[k]

    if k.startswith("f") and k[1:].isdigit():
        n = int(k[1:])
        if 1 <= n <= 24:
            return VK_F1 + (n - 1)

    # Single letter or digit
    if len(k) == 1 and ("a" <= k <= "z" or "0" <= k <= "9"):
        return ord(k.upper())

    return None


def parse_hotkey(text: str) -> Tuple[int, int]:
    """Parse 'Ctrl+Alt+F5' into (mods, vk). Raises ValueError if unsupported."""
    raw = (text or "").strip()
    if not raw:
        raise ValueError("hotkey vide")

    parts = [p.strip() for p in raw.replace("-", "+").split("+") if p.strip()]
    mods = 0

    key_part = None
    for p in parts:
        pl = p.lower()
        if pl in ("ctrl", "control"):
            mods |= MOD_CONTROL
        elif pl == "alt":
            mods |= MOD_ALT
        elif pl == "shift":
            mods |= MOD_SHIFT
        elif pl in ("win", "windows"):
            mods |= MOD_WIN
        else:
            key_part = p

    if key_part is None:
        # last token might be modifier-only (invalid)
        raise ValueError(f"hotkey invalide: {raw}")

    vk = _vk_from_key(key_part)
    if vk is None:
        raise ValueError(
            "Touche non supportée. Utilise par exemple F1..F24, A..Z, 0..9, Enter, Tab, Space, Esc."
        )

    return mods, vk

def _format_win_error(code: int) -> str:
    try:
        buf = ctypes.create_unicode_buffer(1024)
        flags = 0x00001000 | 0x00000200  # FROM_SYSTEM | IGNORE_INSERTS
        kernel32.FormatMessageW(flags, None, code, 0, buf, len(buf), None)
        msg = buf.value.strip()
        return msg or f"winerror={code}"
    except Exception:
        return f"winerror={code}"


class HotkeyManager:
    """Global hotkeys using RegisterHotKey (no keyboard hook).

    Runs a message loop on a dedicated thread.
    """

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._thread_id: Optional[int] = None
        self._callbacks: Dict[int, Callable[[], None]] = {}
        self._registered: Dict[int, Tuple[int, int]] = {}
        self._lock = threading.Lock()
        self._running = threading.Event()
        self._last_error: Optional[str] = None
        self._registration_errors: list[str] = []
        self._ready = threading.Event()

    def get_last_error(self) -> Optional[str]:
        return self._last_error

    def consume_last_error(self) -> Optional[str]:
        error = self._last_error
        self._last_error = None
        return error

    def consume_registration_errors(self) -> list[str]:
        with self._lock:
            errors = list(self._registration_errors)
            self._registration_errors.clear()
            self._last_error = None
        return errors

    def is_alive(self) -> bool:
        """Return True if the message-loop thread is currently running."""
        try:
            return bool(self._thread and self._thread.is_alive())
        except Exception:
            return False

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._ready.clear()
        self._running.set()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        # Wait briefly for the hotkey thread to create its message queue
        self._ready.wait(1.0)

    def stop(self) -> None:
        self._running.clear()
        self._ready.clear()
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread:
            self._thread.join(timeout=1.0)

    def set_hotkey(self, hotkey_id: int, spec: str, callback: Callable[[], None]) -> None:
        """Register or replace a hotkey.

        Important: RegisterHotKey with hwnd=None is *thread-bound*.
        We therefore apply (un)registrations on the hotkey thread itself.
        """
        mods, vk = parse_hotkey(spec)
        with self._lock:
            self._callbacks[hotkey_id] = callback
            self._registered[hotkey_id] = (mods, vk)
        # Apply on hotkey thread if running
        if not self._ready.is_set():
            self._ready.wait(1.0)
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, WM_HK_REGISTER, hotkey_id, 0)

    def clear_hotkey(self, hotkey_id: int) -> None:
        with self._lock:
            self._callbacks.pop(hotkey_id, None)
            self._registered.pop(hotkey_id, None)
        if not self._ready.is_set():
            self._ready.wait(1.0)
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, WM_HK_UNREGISTER, hotkey_id, 0)

    def _apply_registration(self, hotkey_id: int) -> bool:
        with self._lock:
            pair = self._registered.get(hotkey_id)
        if not pair:
            return True
        mods, vk = pair
        try:
            user32.UnregisterHotKey(None, hotkey_id)
        except Exception:
            pass
        ok = user32.RegisterHotKey(None, hotkey_id, mods | MOD_NOREPEAT, vk)
        if not ok:
            code = ctypes.get_last_error()
            self._last_error = f"RegisterHotKey a échoué (id={hotkey_id}, vk={vk}, mods={mods}) : { _format_win_error(code) }"
            with self._lock:
                self._registration_errors.append(self._last_error)
            return False
        return True

    def _register_all(self) -> None:
        with self._lock:
            ids = list(self._registered.keys())
        for hid in ids:
            try:
                self._apply_registration(hid)
            except Exception:
                # Do not crash the hotkey thread
                continue

    def _unregister_all(self) -> None:
        with self._lock:
            ids = list(self._registered.keys())
        for hid in ids:
            try:
                user32.UnregisterHotKey(None, hid)
            except Exception:
                pass

    def _loop(self) -> None:
        self._thread_id = kernel32.GetCurrentThreadId()
        # Make sure the thread has a message queue
        msg = MSG()
        user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_NOREMOVE)

        # Thread is ready to receive WM_HOTKEY / WM_APP messages
        self._ready.set()

        self._register_all()

        while self._running.is_set():
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret == 0:  # WM_QUIT
                break
            if ret == -1:
                break

            if msg.message == WM_HK_REGISTER:
                try:
                    self._apply_registration(int(msg.wParam))
                except Exception:
                    pass
                continue
            if msg.message == WM_HK_UNREGISTER:
                try:
                    user32.UnregisterHotKey(None, int(msg.wParam))
                except Exception:
                    pass
                continue
            if msg.message == WM_HOTKEY:
                hotkey_id = int(msg.wParam)
                cb = None
                with self._lock:
                    cb = self._callbacks.get(hotkey_id)
                if cb:
                    try:
                        cb()
                    except Exception:
                        pass

        self._unregister_all()
