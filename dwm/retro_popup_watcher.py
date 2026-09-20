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
    generation: int = 0


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
    capture_generation: int
    last_check: float
    stable_active: bool
    last_emit: float
    true_streak: int
    false_streak: int


class RetroPopupWatcher:
    """Detect modal popups in stacked Retro windows with generation-safe WGC captures."""

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
        self._captures: Dict[int, WindowsCapture] = {}
        self._capture_controls: Dict[int, CaptureControl] = {}
        self._failures: Dict[int, str] = {}
        self._state: Dict[int, _State] = {}
        self._frames_seen: Dict[int, int] = {}
        self._last_frame_ts: Dict[int, float] = {}
        self._last_has_popup: Dict[int, bool] = {}
        self._capture_generation = 0
        self._closed = False

    def set_enabled(self, enabled: bool) -> None:
        with self._lock:
            if self._closed:
                return
            self._enabled = bool(enabled)

    def update_targets(self, windows: List[WatchedWindow]) -> None:
        """Synchronize targets by HWND + title and stop old controls outside the lock."""
        desired = {int(window.hwnd): window for window in windows if int(window.hwnd)}
        controls_to_stop: list[CaptureControl] = []

        with self._lock:
            if self._closed:
                return

            for hwnd, state in list(self._state.items()):
                wanted = desired.get(hwnd)
                if wanted is None or wanted.title != state.title or wanted.generation != state.generation:
                    control = self._remove_capture_locked(hwnd)
                    if control is not None:
                        controls_to_stop.append(control)

            additions = [
                window
                for hwnd, window in desired.items()
                if hwnd not in self._captures
            ]

        for control in controls_to_stop:
            self._stop_control(control)

        for window in additions:
            self._start_capture(window)

    def _next_capture_generation(self) -> int:
        with self._lock:
            self._capture_generation += 1
            return self._capture_generation

    def _start_capture(self, window: WatchedWindow) -> None:
        hwnd = int(window.hwnd)
        title = str(window.title)
        target_generation = int(window.generation)
        capture_generation = self._next_capture_generation()

        try:
            capture = WindowsCapture(
                cursor_capture=None,
                draw_border=False,
                monitor_index=None,
                window_name=title,
            )
        except Exception as exc:
            with self._lock:
                if not self._closed:
                    self._failures[hwnd] = repr(exc)
            return

        @capture.event  # type: ignore
        def on_frame_arrived(
            frame: Frame,
            capture_control: InternalCaptureControl,
            _hwnd=hwnd,
            _title=title,
            _capture_generation=capture_generation,
        ):
            self._on_frame(_hwnd, _title, _capture_generation, frame)

        @capture.event  # type: ignore
        def on_closed(
            _hwnd=hwnd,
            _capture_generation=capture_generation,
        ):
            control = None
            with self._lock:
                state = self._state.get(_hwnd)
                if state is None or state.capture_generation != _capture_generation:
                    return
                control = self._remove_capture_locked(_hwnd)
            # windows-capture is already closing this control; do not recursively stop it.
            del control

        with self._lock:
            if self._closed or hwnd in self._captures:
                return
            state = _State(
                hwnd=hwnd,
                title=title,
                generation=target_generation,
                capture_generation=capture_generation,
                last_check=0.0,
                stable_active=False,
                last_emit=0.0,
                true_streak=0,
                false_streak=0,
            )
            self._captures[hwnd] = capture
            self._state[hwnd] = state
            self._failures.pop(hwnd, None)
            self._frames_seen[hwnd] = 0
            self._last_frame_ts[hwnd] = 0.0
            self._last_has_popup[hwnd] = False

        try:
            control = capture.start_free_threaded()
        except Exception as exc:
            with self._lock:
                state = self._state.get(hwnd)
                if state is not None and state.capture_generation == capture_generation:
                    self._remove_capture_locked(hwnd)
                    self._failures[hwnd] = repr(exc)
            return

        should_stop = False
        with self._lock:
            state = self._state.get(hwnd)
            if (
                self._closed
                or state is None
                or state.capture_generation != capture_generation
            ):
                should_stop = True
            else:
                self._capture_controls[hwnd] = control
        if should_stop:
            self._stop_control(control)

    def _remove_capture_locked(self, hwnd: int) -> CaptureControl | None:
        self._captures.pop(hwnd, None)
        control = self._capture_controls.pop(hwnd, None)
        self._state.pop(hwnd, None)
        self._failures.pop(hwnd, None)
        self._frames_seen.pop(hwnd, None)
        self._last_frame_ts.pop(hwnd, None)
        self._last_has_popup.pop(hwnd, None)
        return control

    @staticmethod
    def _stop_control(control: CaptureControl) -> None:
        try:
            control.stop()
        except Exception:
            pass

    def shutdown(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._enabled = False
            controls = list(self._capture_controls.values())
            self._captures.clear()
            self._capture_controls.clear()
            self._state.clear()
            self._frames_seen.clear()
            self._last_frame_ts.clear()
            self._last_has_popup.clear()
            self._failures.clear()
        for control in controls:
            self._stop_control(control)

    def _on_frame(self, hwnd: int, title: str, capture_generation: int, frame: Frame) -> None:
        now = time.monotonic()
        with self._lock:
            state = self._state.get(hwnd)
            if (
                self._closed
                or state is None
                or state.capture_generation != capture_generation
                or not self._enabled
            ):
                return
            if (now - state.last_check) < self._min_dt:
                return
            state.last_check = now
            target_generation = state.generation

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
            state = self._state.get(hwnd)
            if (
                self._closed
                or state is None
                or state.capture_generation != capture_generation
                or state.generation != target_generation
                or state.title != title
                or not self._enabled
            ):
                return

            self._frames_seen[hwnd] = self._frames_seen.get(hwnd, 0) + 1
            self._last_frame_ts[hwnd] = now
            self._last_has_popup[hwnd] = has_popup

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

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "enabled": bool(self._enabled),
                "targets": [state.title for state in self._state.values()],
                "frames_seen": {
                    self._state[hwnd].title: count
                    for hwnd, count in self._frames_seen.items()
                    if hwnd in self._state
                },
                "last_frame_ts": {
                    self._state[hwnd].title: value
                    for hwnd, value in self._last_frame_ts.items()
                    if hwnd in self._state
                },
                "last_has_popup": {
                    self._state[hwnd].title: value
                    for hwnd, value in self._last_has_popup.items()
                    if hwnd in self._state
                },
                "failures": {
                    self._state[hwnd].title if hwnd in self._state else str(hwnd): value
                    for hwnd, value in self._failures.items()
                },
            }
