from __future__ import annotations

import ctypes
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from ctypes import wintypes

from ..models import GameWindow


PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
TOKEN_QUERY = 0x0008
TOKEN_ELEVATION = 20
MONITOR_DEFAULTTONEAREST = 2
DWMWA_CLOAKED = 14
GWL_STYLE = -16
GWL_EXSTYLE = -20
WS_EX_TOPMOST = 0x00000008
GW_OWNER = 4
GW_HWNDNEXT = 2
GA_ROOT = 2
MONITORINFOF_PRIMARY = 0x00000001
WDA_EXCLUDEFROMCAPTURE = 0x00000011


@dataclass(frozen=True)
class RectSnapshot:
    left: int = 0
    top: int = 0
    right: int = 0
    bottom: int = 0

    @property
    def width(self) -> int:
        return max(0, self.right - self.left)

    @property
    def height(self) -> int:
        return max(0, self.bottom - self.top)


@dataclass(frozen=True)
class WindowTelemetry:
    hwnd: int
    session_id: str
    game_mode: str
    title: str
    window_class: str
    pseudo: str
    character_class: str
    pid: int = 0
    thread_id: int = 0
    process_path: str = ""
    process_name: str = ""
    process_created_100ns: int = 0
    process_elevated: bool | None = None
    process_session_id: int = 0
    process_architecture: str = ""
    owner_hwnd: int = 0
    root_hwnd: int = 0
    z_order_index: int = -1
    window_rect: RectSnapshot = RectSnapshot()
    client_rect_screen: RectSnapshot = RectSnapshot()
    visible: bool = False
    enabled: bool = False
    minimized: bool = False
    maximized: bool = False
    foreground: bool = False
    hung: bool = False
    cloaked: bool = False
    topmost: bool = False
    display_affinity: int = 0
    capture_excluded: bool = False
    style: int = 0
    ex_style: int = 0
    dpi: int = 96
    monitor_device: str = ""
    monitor_primary: bool = False
    monitor_rect: RectSnapshot = RectSnapshot()
    monitor_work_rect: RectSnapshot = RectSnapshot()

    @property
    def obs_executable(self) -> str:
        return self.process_name or Path(self.process_path).name

    @property
    def obs_window_selector(self) -> str:
        return encode_obs_window_selector(
            self.title,
            self.window_class,
            self.obs_executable,
        )

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["window_rect"]["width"] = self.window_rect.width
        data["window_rect"]["height"] = self.window_rect.height
        data["client_rect_screen"]["width"] = self.client_rect_screen.width
        data["client_rect_screen"]["height"] = self.client_rect_screen.height
        data["monitor_rect"]["width"] = self.monitor_rect.width
        data["monitor_rect"]["height"] = self.monitor_rect.height
        data["monitor_work_rect"]["width"] = self.monitor_work_rect.width
        data["monitor_work_rect"]["height"] = self.monitor_work_rect.height
        data["obs_executable"] = self.obs_executable
        data["obs_window_selector"] = self.obs_window_selector
        return data


def _encode_obs_component(value: str) -> str:
    # OBS/libobs window-helpers.c escapes # first, then :.
    return str(value or "").replace("#", "#22").replace(":", "#3A")


def encode_obs_window_selector(title: str, window_class: str, executable: str) -> str:
    return ":".join(
        (
            _encode_obs_component(title),
            _encode_obs_component(window_class),
            _encode_obs_component(executable),
        )
    )


def _rect(value) -> RectSnapshot:
    return RectSnapshot(
        left=int(value.left),
        top=int(value.top),
        right=int(value.right),
        bottom=int(value.bottom),
    )


def _filetime_value(value) -> int:
    return (int(value.dwHighDateTime) << 32) | int(value.dwLowDateTime)


def _collect_process_details(pid: int) -> tuple[str, int, bool | None, int, str]:
    if os.name != "nt" or not pid:
        return "", 0, None, 0, ""

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)

    OpenProcess = kernel32.OpenProcess
    OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    OpenProcess.restype = wintypes.HANDLE
    CloseHandle = kernel32.CloseHandle
    CloseHandle.argtypes = (wintypes.HANDLE,)
    CloseHandle.restype = wintypes.BOOL
    QueryFullProcessImageNameW = kernel32.QueryFullProcessImageNameW
    QueryFullProcessImageNameW.argtypes = (
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    )
    QueryFullProcessImageNameW.restype = wintypes.BOOL
    GetProcessTimes = kernel32.GetProcessTimes
    GetProcessTimes.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
    )
    GetProcessTimes.restype = wintypes.BOOL

    process = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not process:
        return "", 0, None, 0, ""

    path = ""
    created = 0
    elevated: bool | None = None
    process_session_id = 0
    process_architecture = ""
    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if QueryFullProcessImageNameW(process, 0, buffer, ctypes.byref(size)):
            path = buffer.value or ""

        creation = wintypes.FILETIME()
        exit_time = wintypes.FILETIME()
        kernel = wintypes.FILETIME()
        user = wintypes.FILETIME()
        if GetProcessTimes(
            process,
            ctypes.byref(creation),
            ctypes.byref(exit_time),
            ctypes.byref(kernel),
            ctypes.byref(user),
        ):
            created = _filetime_value(creation)

        token = wintypes.HANDLE()
        OpenProcessToken = advapi32.OpenProcessToken
        OpenProcessToken.argtypes = (
            wintypes.HANDLE,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.HANDLE),
        )
        OpenProcessToken.restype = wintypes.BOOL
        if OpenProcessToken(process, TOKEN_QUERY, ctypes.byref(token)):
            try:
                class TOKEN_ELEVATION_STRUCT(ctypes.Structure):
                    _fields_ = [("TokenIsElevated", wintypes.DWORD)]

                value = TOKEN_ELEVATION_STRUCT()
                returned = wintypes.DWORD()
                GetTokenInformation = advapi32.GetTokenInformation
                GetTokenInformation.argtypes = (
                    wintypes.HANDLE,
                    ctypes.c_int,
                    wintypes.LPVOID,
                    wintypes.DWORD,
                    ctypes.POINTER(wintypes.DWORD),
                )
                GetTokenInformation.restype = wintypes.BOOL
                if GetTokenInformation(
                    token,
                    TOKEN_ELEVATION,
                    ctypes.byref(value),
                    ctypes.sizeof(value),
                    ctypes.byref(returned),
                ):
                    elevated = bool(value.TokenIsElevated)
            finally:
                CloseHandle(token)

        session_value = wintypes.DWORD()
        ProcessIdToSessionId = kernel32.ProcessIdToSessionId
        ProcessIdToSessionId.argtypes = (
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        )
        ProcessIdToSessionId.restype = wintypes.BOOL
        if ProcessIdToSessionId(pid, ctypes.byref(session_value)):
            process_session_id = int(session_value.value)

        IsWow64Process2 = getattr(kernel32, "IsWow64Process2", None)
        if IsWow64Process2 is not None:
            process_machine = ctypes.c_ushort()
            native_machine = ctypes.c_ushort()
            IsWow64Process2.argtypes = (
                wintypes.HANDLE,
                ctypes.POINTER(ctypes.c_ushort),
                ctypes.POINTER(ctypes.c_ushort),
            )
            IsWow64Process2.restype = wintypes.BOOL
            if IsWow64Process2(
                process,
                ctypes.byref(process_machine),
                ctypes.byref(native_machine),
            ):
                machine = int(process_machine.value or native_machine.value)
                process_architecture = {
                    0x014C: "x86",
                    0x8664: "x64",
                    0xAA64: "arm64",
                }.get(machine, f"0x{machine:04X}" if machine else "")
    finally:
        CloseHandle(process)

    return path, created, elevated, process_session_id, process_architecture


def collect_window_telemetry(window: GameWindow, game_mode: str) -> WindowTelemetry:
    hwnd = int(window.hwnd)
    mode = (game_mode or "unity").strip().lower()
    if os.name != "nt":
        return WindowTelemetry(
            hwnd=hwnd,
            session_id=f"0:0:{hwnd}",
            game_mode=mode,
            title=window.title,
            window_class="",
            pseudo=window.pseudo,
            character_class=window.character_class,
        )

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    dwmapi = ctypes.WinDLL("dwmapi", use_last_error=True)

    GetWindowThreadProcessId = user32.GetWindowThreadProcessId
    GetWindowThreadProcessId.argtypes = (
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD),
    )
    GetWindowThreadProcessId.restype = wintypes.DWORD

    pid_value = wintypes.DWORD()
    thread_id = int(
        GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid_value))
    )
    pid = int(pid_value.value)

    GetForegroundWindow = user32.GetForegroundWindow
    GetForegroundWindow.argtypes = ()
    GetForegroundWindow.restype = wintypes.HWND
    GetWindow = user32.GetWindow
    GetWindow.argtypes = (wintypes.HWND, wintypes.UINT)
    GetWindow.restype = wintypes.HWND
    GetAncestor = user32.GetAncestor
    GetAncestor.argtypes = (wintypes.HWND, wintypes.UINT)
    GetAncestor.restype = wintypes.HWND

    class_buffer = ctypes.create_unicode_buffer(512)
    user32.GetClassNameW(wintypes.HWND(hwnd), class_buffer, len(class_buffer))
    window_class = class_buffer.value or ""

    owner_hwnd = int(GetWindow(wintypes.HWND(hwnd), GW_OWNER) or 0)
    root_hwnd = int(GetAncestor(wintypes.HWND(hwnd), GA_ROOT) or 0)

    GetTopWindow = user32.GetTopWindow
    GetTopWindow.argtypes = (wintypes.HWND,)
    GetTopWindow.restype = wintypes.HWND

    z_order_index = -1
    top_window = GetTopWindow(None)
    current = int(top_window or 0)
    for index in range(4096):
        if not current:
            break
        if current == hwnd:
            z_order_index = index
            break
        current = int(GetWindow(wintypes.HWND(current), GW_HWNDNEXT) or 0)

    (
        process_path,
        process_created,
        process_elevated,
        process_session_id,
        process_architecture,
    ) = _collect_process_details(pid)
    process_name = Path(process_path).name if process_path else ""

    window_rect_value = wintypes.RECT()
    user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(window_rect_value))

    client_rect_value = wintypes.RECT()
    client_screen = RectSnapshot()
    if user32.GetClientRect(wintypes.HWND(hwnd), ctypes.byref(client_rect_value)):
        top_left = wintypes.POINT(client_rect_value.left, client_rect_value.top)
        bottom_right = wintypes.POINT(client_rect_value.right, client_rect_value.bottom)
        if user32.ClientToScreen(wintypes.HWND(hwnd), ctypes.byref(top_left)) and user32.ClientToScreen(
            wintypes.HWND(hwnd), ctypes.byref(bottom_right)
        ):
            client_screen = RectSnapshot(
                left=int(top_left.x),
                top=int(top_left.y),
                right=int(bottom_right.x),
                bottom=int(bottom_right.y),
            )

    getter = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
    getter.argtypes = (wintypes.HWND, ctypes.c_int)
    getter.restype = ctypes.c_ssize_t
    style = int(getter(wintypes.HWND(hwnd), GWL_STYLE))
    ex_style = int(getter(wintypes.HWND(hwnd), GWL_EXSTYLE))

    dpi = 96
    get_dpi = getattr(user32, "GetDpiForWindow", None)
    if get_dpi is not None:
        get_dpi.argtypes = (wintypes.HWND,)
        get_dpi.restype = wintypes.UINT
        value = int(get_dpi(wintypes.HWND(hwnd)) or 0)
        if value > 0:
            dpi = value

    cloaked_value = wintypes.DWORD()
    cloaked = False
    try:
        result = dwmapi.DwmGetWindowAttribute(
            wintypes.HWND(hwnd),
            DWMWA_CLOAKED,
            ctypes.byref(cloaked_value),
            ctypes.sizeof(cloaked_value),
        )
        cloaked = result == 0 and bool(cloaked_value.value)
    except Exception:
        cloaked = False

    monitor_device = ""
    monitor_rect = RectSnapshot()
    monitor_work_rect = RectSnapshot()

    class MONITORINFOEXW(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("rcMonitor", wintypes.RECT),
            ("rcWork", wintypes.RECT),
            ("dwFlags", wintypes.DWORD),
            ("szDevice", wintypes.WCHAR * 32),
        ]

    MonitorFromWindow = user32.MonitorFromWindow
    MonitorFromWindow.argtypes = (wintypes.HWND, wintypes.DWORD)
    MonitorFromWindow.restype = wintypes.HANDLE
    GetMonitorInfoW = user32.GetMonitorInfoW
    GetMonitorInfoW.argtypes = (wintypes.HANDLE, ctypes.c_void_p)
    GetMonitorInfoW.restype = wintypes.BOOL

    monitor_primary = False
    monitor = MonitorFromWindow(
        wintypes.HWND(hwnd),
        MONITOR_DEFAULTTONEAREST,
    )
    if monitor:
        info = MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(info)
        if GetMonitorInfoW(monitor, ctypes.byref(info)):
            monitor_device = info.szDevice
            monitor_primary = bool(info.dwFlags & MONITORINFOF_PRIMARY)
            monitor_rect = _rect(info.rcMonitor)
            monitor_work_rect = _rect(info.rcWork)

    display_affinity = wintypes.DWORD()
    affinity_value = 0
    get_affinity = getattr(user32, "GetWindowDisplayAffinity", None)
    if get_affinity is not None:
        get_affinity.argtypes = (
            wintypes.HWND,
            ctypes.POINTER(wintypes.DWORD),
        )
        get_affinity.restype = wintypes.BOOL
        if get_affinity(wintypes.HWND(hwnd), ctypes.byref(display_affinity)):
            affinity_value = int(display_affinity.value)

    session_id = f"{pid}:{process_created}:{hwnd}"
    return WindowTelemetry(
        hwnd=hwnd,
        session_id=session_id,
        game_mode=mode,
        title=window.title,
        window_class=window_class,
        pseudo=window.pseudo,
        character_class=window.character_class,
        pid=pid,
        thread_id=thread_id,
        process_path=process_path,
        process_name=process_name,
        process_created_100ns=process_created,
        process_elevated=process_elevated,
        process_session_id=process_session_id,
        process_architecture=process_architecture,
        owner_hwnd=owner_hwnd,
        root_hwnd=root_hwnd,
        z_order_index=z_order_index,
        window_rect=_rect(window_rect_value),
        client_rect_screen=client_screen,
        visible=bool(user32.IsWindowVisible(wintypes.HWND(hwnd))),
        enabled=bool(user32.IsWindowEnabled(wintypes.HWND(hwnd))),
        minimized=bool(user32.IsIconic(wintypes.HWND(hwnd))),
        maximized=bool(user32.IsZoomed(wintypes.HWND(hwnd))),
        foreground=int(GetForegroundWindow() or 0) == hwnd,
        hung=bool(user32.IsHungAppWindow(wintypes.HWND(hwnd))),
        cloaked=cloaked,
        topmost=bool(ex_style & WS_EX_TOPMOST),
        display_affinity=affinity_value,
        capture_excluded=affinity_value == WDA_EXCLUDEFROMCAPTURE,
        style=style,
        ex_style=ex_style,
        dpi=dpi,
        monitor_device=monitor_device,
        monitor_primary=monitor_primary,
        monitor_rect=monitor_rect,
        monitor_work_rect=monitor_work_rect,
    )
