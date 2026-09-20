from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, Dict, List

import numpy as np

from windows_capture import CaptureControl, Frame, InternalCaptureControl, WindowsCapture  # type: ignore

from .retro_popup_detector import detect_retro_modal_popup


@dataclass(frozen=True)
class WatchedWindow:
    hwnd: int
    title: str


@dataclass(frozen=True)
class PopupEvent:
    hwnd: int
    title: str
    ts: float
    generation: int = 0


@dataclass
class _State:
    hwnd: int
    title: str
    generation: int
    last_check: float
    stable_active: bool
    last_emit: float
    true_streak: int
    false_streak: int


_CaptureKey = tuple[int, int]


class RetroPopupWatcher:
    """Detect Retro modal popups without transferring captures between HWNDs."""

    def __init__(
        self,
        emit: Callable[[PopupEvent], None],
        max_fps_per_window: float = 4.0,
        cooldown_sec: float = 2.0,
        true_needed: int = 2,
        false_needed: int = 3,
    ):
        self._emit = emit
        self._enabled = False
        self._lock = threading.RLock()
        self._min_dt = 1.0 / max(0.5, float(max_fps_per_window))
        self._cooldown = float(cooldown_sec)
        self._true_needed = max(1, int(true_needed))
        self._false_needed = max(1, int(false_needed))
        self._next_generation = 0

        self._captures: Dict[_CaptureKey, WindowsCapture] = {}
        self._capture_controls: Dict[_CaptureKey, CaptureControl] = {}
        self._state: Dict[_CaptureKey, _State] = {}
        self._failures: Dict[_CaptureKey, str] = {}
        self._frames_seen: Dict[_CaptureKey, int] = {}
        self._last_frame_ts: Dict[_CaptureKey, float] = {}
        self._last_has_popup: Dict[_CaptureKey, bool] = {}

    def set_enabled(self, enabled: bool) -> None:
        with self._lock:
            self._enabled = bool(enabled)

    def _drop_key_locked(self, key: _CaptureKey) -> CaptureControl | None:
        self._captures.pop(key, None)
        control = self._capture_controls.pop(key, None)
        self._state.pop(key, None)
        self._failures.pop(key, None)
        self._frames_seen.pop(key, None)
        self._last_frame_ts.pop(key, None)
        self._last_has_popup.pop(key, None)
        return control

    @staticmethod
    def _stop_controls(controls: List[CaptureControl]) -> None:
        for control in controls:
            try:
                control.stop()
            except Exception:
                pass

    def update_targets(self, windows: List[WatchedWindow]) -> None:
        """Synchronize captures by HWND+generation; title is only the WGC API selector."""
        wanted = {
            int(window.hwnd): WatchedWindow(int(window.hwnd), str(window.title))
            for window in windows
            if int(window.hwnd) and str(window.title)
        }
        controls_to_stop: List[CaptureControl] = []
        additions: list[tuple[_CaptureKey, WatchedWindow]] = []

        with self._lock:
            retained_hwnds: set[int] = set()
            for key, state in list(self._state.items()):
                target = wanted.get(state.hwnd)
                if target is not None and target.title == state.title:
                    retained_hwnds.add(state.hwnd)
                    continue
                control = self._drop_key_locked(key)
                if control is not None:
                    controls_to_stop.append(control)

            for hwnd, target in wanted.items():
                if hwnd in retained_hwnds:
                    continue
                self._next_generation += 1
                key = (hwnd, self._next_generation)
                self._state[key] = _State(
                    hwnd=hwnd,
                    title=target.title,
                    generation=key[1],
                    last_check=0.0,
                    stable_active=False,
                    last_emit=0.0,
                    true_streak=0,
                    false_streak=0,
                )
                self._frames_seen[key] = 0
                self._last_frame_ts[key] = 0.0
                self._last_has_popup[key] = False
                additions.append((key, target))

        # CaptureControl.stop() may synchronously wait for callbacks. Never hold
        # the watcher lock while calling it.
        self._stop_controls(controls_to_stop)

        for key, target in additions:
            self._start_capture(key, target)

    def _start_capture(self, key: _CaptureKey, target: WatchedWindow) -> None:
        try:
            capture = WindowsCapture(
                cursor_capture=None,
                draw_border=False,
                monitor_index=None,
                window_name=target.title,
            )
        except Exception as exc:
            with self._lock:
                if key in self._state:
                    self._failures[key] = repr(exc)
            return

        @capture.event  # type: ignore
        def on_frame_arrived(
            frame: Frame,
            capture_control: InternalCaptureControl,
            _key=key,
        ):
            del capture_control
            self._on_frame(_key, frame)

        @capture.event  # type: ignore
        def on_closed(_key=key):
            with self._lock:
                self._drop_key_locked(_key)

        try:
            control = capture.start_free_threaded()
        except Exception as exc:
            with self._lock:
                if key in self._state:
                    self._failures[key] = repr(exc)
                    self._drop_key_locked(key)
            return

        stale = False
        with self._lock:
            state = self._state.get(key)
            if state is None or state.hwnd != target.hwnd or state.title != target.title:
                stale = True
            else:
                self._captures[key] = capture
                self._capture_controls[key] = control
                self._failures.pop(key, None)
        if stale:
            self._stop_controls([control])

    def shutdown(self) -> None:
        with self._lock:
            self._enabled = False
            controls = list(self._capture_controls.values())
            self._captures.clear()
            self._capture_controls.clear()
            self._state.clear()
            self._frames_seen.clear()
            self._last_frame_ts.clear()
            self._last_has_popup.clear()
            self._failures.clear()
        self._stop_controls(controls)

    def _on_frame(self, key: _CaptureKey, frame: Frame) -> None:
        now = time.monotonic()
        with self._lock:
            state = self._state.get(key)
            if state is None or state.generation != key[1] or not self._enabled:
                return
            if (now - state.last_check) < self._min_dt:
                return
            state.last_check = now

        try:
            bgr_frame = frame.convert_to_bgr()
            img: np.ndarray = bgr_frame.frame_buffer
        except Exception:
            return

        try:
            has_popup = bool(detect_retro_modal_popup(img))
        except Exception:
            has_popup = False

        event: PopupEvent | None = None
        with self._lock:
            state = self._state.get(key)
            if state is None or state.generation != key[1] or not self._enabled:
                return

            self._frames_seen[key] = self._frames_seen.get(key, 0) + 1
            self._last_frame_ts[key] = now
            self._last_has_popup[key] = has_popup

            if has_popup:
                state.true_streak += 1
                state.false_streak = 0
            else:
                state.false_streak += 1
                state.true_streak = 0

            if not state.stable_active:
                if state.true_streak >= self._true_needed:
                    state.stable_active = True
                    state.true_streak = 0
                    if (now - state.last_emit) >= self._cooldown:
                        state.last_emit = now
                        event = PopupEvent(
                            hwnd=state.hwnd,
                            title=state.title,
                            ts=now,
                            generation=state.generation,
                        )
            elif state.false_streak >= self._false_needed:
                state.stable_active = False
                state.false_streak = 0

        if event is not None:
            try:
                self._emit(event)
            except Exception:
                pass

    def is_current_event(self, event: PopupEvent) -> bool:
        """Revalidate that a detection still belongs to the active capture generation."""
        with self._lock:
            key = (int(event.hwnd), int(event.generation))
            state = self._state.get(key)
            return bool(
                self._enabled
                and state is not None
                and state.hwnd == int(event.hwnd)
                and state.title == str(event.title)
                and state.generation == int(event.generation)
            )

    def get_stats(self) -> dict:
        """Return lightweight title-oriented stats for debugging."""
        with self._lock:
            def labels(values):
                return {
                    f"{self._state[key].title}#{key[0]}@{key[1]}": value
                    for key, value in values.items()
                    if key in self._state
                }

            return {
                "enabled": bool(self._enabled),
                "targets": [
                    f"{state.title}#{state.hwnd}@{state.generation}"
                    for state in self._state.values()
                ],
                "frames_seen": labels(self._frames_seen),
                "last_frame_ts": labels(self._last_frame_ts),
                "last_has_popup": labels(self._last_has_popup),
                "failures": labels(self._failures),
            }
