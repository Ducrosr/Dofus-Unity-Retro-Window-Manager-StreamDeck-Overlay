from __future__ import annotations

import re
import unicodedata
from typing import List

from .win32_enum import enum_top_level_windows, get_class_name

from ..models import GameWindow


# -------------------------- Win32 helpers (pid / privileges) --------------------------

def _is_admin() -> bool:
    """Best-effort admin check (Windows only)."""
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _get_pid(hwnd: int) -> int:
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        GetWindowThreadProcessId = user32.GetWindowThreadProcessId
        GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]

        pid = wintypes.DWORD(0)
        GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
        return int(pid.value)
    except Exception:
        return 0


def suspect_privilege_mismatch(hwnds: list[int]) -> bool:
    """Heuristic: detect likely admin/non-admin mismatch.

    If this process is NOT elevated and at least one target window's process
    denies PROCESS_QUERY_LIMITED_INFORMATION (Access Denied), it usually means
    the target is elevated (admin) and focus/hotkeys can be impacted.
    """
    try:
        if _is_admin():
            return False

        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        OpenProcess = kernel32.OpenProcess
        OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        OpenProcess.restype = wintypes.HANDLE
        CloseHandle = kernel32.CloseHandle
        CloseHandle.argtypes = [wintypes.HANDLE]
        CloseHandle.restype = wintypes.BOOL

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

        for hwnd in hwnds[:10]:
            pid = _get_pid(hwnd)
            if not pid:
                continue
            h = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not h:
                err = ctypes.get_last_error()
                if err == 5:  # ACCESS_DENIED
                    return True
                continue
            CloseHandle(h)
        return False
    except Exception:
        return False


def extract_pseudo(title: str) -> str:
    """Generic heuristic: pseudo is first token of the window title."""
    title = (title or "").strip()
    if not title:
        return ""
    return title.split()[0]


_CHARACTER_CLASSES = (
    "Féca",
    "Osamodas",
    "Enutrof",
    "Sram",
    "Xélor",
    "Ecaflip",
    "Eniripsa",
    "Iop",
    "Crâ",
    "Sadida",
    "Sacrieur",
    "Pandawa",
    "Roublard",
    "Zobal",
    "Steamer",
    "Eliotrope",
    "Huppermage",
    "Ouginak",
    "Forgelance",
)


def _normalized_words(value: str) -> list[str]:
    decomposed = unicodedata.normalize("NFKD", value or "")
    without_accents = "".join(character for character in decomposed if not unicodedata.combining(character))
    return re.findall(r"[a-z]+", without_accents.casefold())


_CLASS_BY_WORD = {_normalized_words(name)[0]: name for name in _CHARACTER_CLASSES}

_UNITY_TITLE_SEPARATOR = re.compile(r"\s+(?:-|–|—|\|)\s+")
_UNITY_SYSTEM_WORDS = {"dofus", "release", "beta", "unity", "ankama", "launcher"}


def _is_unity_metadata_part(value: str) -> bool:
    """Return True for title parts that cannot be a character name."""
    stripped = (value or "").strip()
    if not stripped:
        return True
    if re.fullmatch(r"v?\d+(?:\.\d+)+", stripped, flags=re.IGNORECASE):
        return True
    words = set(_normalized_words(stripped))
    return bool(words & _UNITY_SYSTEM_WORDS)


def extract_pseudo_unity(title: str) -> str:
    """Extract the Unity character name independently of title-part order.

    Dofus normally exposes ``Name - Class - Version``, but some releases or
    configurations expose ``Class - Name - Version``. The class part is used
    as an anchor so both formats yield the same character name.
    """
    stripped = (title or "").strip()
    if not stripped:
        return ""

    parts = [part.strip() for part in _UNITY_TITLE_SEPARATOR.split(stripped) if part.strip()]
    class_part_indexes = [
        index for index, part in enumerate(parts) if any(word in _CLASS_BY_WORD for word in _normalized_words(part))
    ]

    for class_index in class_part_indexes:
        # The name is most commonly immediately before the class. Looking on
        # both sides also supports titles that put the class first.
        for candidate_index in (class_index - 1, class_index + 1):
            if candidate_index < 0 or candidate_index >= len(parts):
                continue
            candidate = parts[candidate_index]
            candidate_words = _normalized_words(candidate)
            if _is_unity_metadata_part(candidate):
                continue
            if any(word in _CLASS_BY_WORD for word in candidate_words):
                continue
            return extract_pseudo(candidate)

    # If no usable class anchor exists, prefer the first non-metadata part and
    # retain the former first-token behaviour as a final fallback.
    for part in parts:
        if not _is_unity_metadata_part(part):
            return extract_pseudo(part)
    return extract_pseudo(stripped)


def extract_character_class(title: str, pseudo: str = "") -> str:
    """Extract a canonical French Dofus class name from a window title.

    The title format can evolve, so detection is delimiter-agnostic and
    accent-insensitive. Words belonging to a leading pseudo are skipped to
    avoid treating a character named, for example, "Iop" as its class.
    """
    title_words = _normalized_words(title)
    pseudo_words = _normalized_words(pseudo)
    if pseudo_words and title_words[: len(pseudo_words)] == pseudo_words:
        title_words = title_words[len(pseudo_words) :]

    for word in title_words:
        character_class = _CLASS_BY_WORD.get(word)
        if character_class:
            return character_class
    return ""


def extract_pseudo_retro(title: str) -> str:
    """Heuristic for Retro.

    In many setups, Retro titles include the client version, e.g.:
      - 'Pseudo - Dofus Retro v1.XX'
      - 'Dofus Retro v1.XX - Pseudo'
      - 'Pseudo - Dofus Retro v1.XX - Serveur'

    We try to pick the part that is *not* the 'Dofus Retro v…' segment.
    """
    t = (title or "").strip()
    if not t:
        return ""

    parts = [p.strip() for p in t.split(" - ") if p.strip()]
    if parts:
        # Remove the segment that clearly identifies Retro.
        lowered = [p.lower() for p in parts]
        keep = [parts[i] for i, lp in enumerate(lowered) if "dofus retro v" not in lp]

        # If we removed something, the remaining part often starts with pseudo.
        if keep:
            return extract_pseudo(keep[0])

        # Fallback: if everything contains the marker, pick first token.
        return extract_pseudo(parts[0])

    return extract_pseudo(t)


# -------------------------- Win32 helpers (process path) --------------------------

def _get_process_image_path(hwnd: int) -> str:
    """Best-effort: returns full process image path for a window handle (may be empty)."""
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        GetWindowThreadProcessId = user32.GetWindowThreadProcessId
        GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]

        OpenProcess = kernel32.OpenProcess
        OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        OpenProcess.restype = wintypes.HANDLE

        QueryFullProcessImageNameW = kernel32.QueryFullProcessImageNameW
        QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        QueryFullProcessImageNameW.restype = wintypes.BOOL

        CloseHandle = kernel32.CloseHandle
        CloseHandle.argtypes = [wintypes.HANDLE]
        CloseHandle.restype = wintypes.BOOL

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

        pid = wintypes.DWORD(0)
        GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
        if not pid.value:
            return ""

        hproc = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not hproc:
            return ""

        try:
            size = wintypes.DWORD(4096)
            buf = ctypes.create_unicode_buffer(size.value)
            if QueryFullProcessImageNameW(hproc, 0, buf, ctypes.byref(size)):
                return buf.value or ""
            return ""
        finally:
            CloseHandle(hproc)
    except Exception:
        return ""


# -------------------------- Window enumeration --------------------------

def list_unity_windows(class_name: str = "UnityWndClass") -> List[GameWindow]:
    """Return Dofus Unity windows detected through the native Win32 API."""
    out: List[GameWindow] = []
    seen = set()

    for hwnd, title in enum_top_level_windows(class_name=class_name, visible_only=True):
        if hwnd in seen:
            continue
        seen.add(hwnd)
        pseudo = extract_pseudo_unity(title)
        character_class = extract_character_class(title, pseudo)
        out.append(GameWindow(hwnd=hwnd, title=title, pseudo=pseudo, character_class=character_class))

    return out


def list_retro_windows(
    class_name: str = "Chrome_WidgetWin_1",
    title_keyword: str = "dofus retro v",
    process_keyword: str = "",
) -> List[GameWindow]:
    """Return detected Dofus Retro windows.

    Note: Chrome_WidgetWin_1 is used by many Chromium/Electron apps, so we apply
    a strong title filter by default (expected to contain 'Dofus Retro v').

    If you *really* need it, you can provide a process_keyword as a fallback.
    """
    title_kw = (title_keyword or "dofus retro v").lower()
    proc_kw = (process_keyword or "").lower()

    out: List[GameWindow] = []
    seen = set()

    candidates = enum_top_level_windows(class_name=class_name, visible_only=True)

    for hwnd, title in candidates:
        if not title:
            continue
        if hwnd in seen:
            continue

        # Filtering:
        # - Prefer a strict title match (reduces false positives a lot).
        # - Optionally fallback on process path if title_keyword is empty.
        ok = False
        t = title.lower()
        if title_kw:
            ok = title_kw in t
        else:
            if proc_kw:
                p = _get_process_image_path(hwnd).lower()
                if p and proc_kw in p:
                    ok = True
        if not ok:
            continue

        seen.add(hwnd)
        pseudo = extract_pseudo_retro(title)
        character_class = extract_character_class(title, pseudo)
        out.append(GameWindow(hwnd=hwnd, title=title, pseudo=pseudo, character_class=character_class))

    return out


def list_game_windows(
    game_mode: str,
    retro_title_keyword: str = "dofus retro v",
    retro_process_keyword: str = "",
) -> List[GameWindow]:
    gm = (game_mode or "unity").strip().lower()
    if gm == "retro":
        return list_retro_windows(
            class_name="Chrome_WidgetWin_1",
            title_keyword=retro_title_keyword,
            process_keyword=retro_process_keyword,
        )
    return list_unity_windows(class_name="UnityWndClass")


def list_visible_dofus_candidates() -> list[tuple[int, str, str]]:
    """Return visible Dofus-titled windows that did not match the active scanner."""
    candidates = []
    for hwnd, title in enum_top_level_windows(class_name=None, visible_only=True):
        lowered = title.lower()
        if "dofus" not in lowered or "dofus window manager" in lowered:
            continue
        candidates.append((hwnd, title, get_class_name(hwnd)))
    return candidates
