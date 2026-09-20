from __future__ import annotations

import time
import threading
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


class RetroPopupWatcher:
    """Detect Retro modal popups without reusing a capture across HWND identities."""

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
        self._next_generation = 1

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

    def set_enabled(self, enabled: bool) -> None:
        with self._lock:
            self._enabled = bool(enabled)

    def _new_generation_locked(self) -> int:
        generation = self._next_generation
        self._next_generation += 1
        return generation

    def _detach_locked(self, hwnd: int) -> CaptureControl | None:
        self._captures.pop(hwnd, None)
        control = self._capture_controls.pop(hwnd, None)
        self._state.pop(hwnd, None)
        self._failures.pop(hwnd, None)
        self._frames_seen.pop(hwnd, None)
        self._last_frame_ts.pop(hwnd, None)
        self._last_has_popup.pop(hwnd, None)
        return control

    @staticmethod
    def _stop_controls(controls: list[CaptureControl]) -> None:
        for control in controls:
            try:
                control.stop()
            except Exception:
                pass

    def update_targets(self, windows: List[WatchedWindow]) -> None:
        """Synchronize captures by HWND identity; title remains WGC's selector."""
        wanted = {int(window.hwnd): str(window.title) for window in windows if window.title}
        controls_to_stop: list[CaptureControl] = []
        to_add: list[tuple[int, str, int]] = []

        with self._lock:
            for hwnd, state in list(self._state.items()):
                wanted_title = wanted.get(hwnd)
                if wanted_title is None or wanted_title != state.title:
                    control = self._detach_locked(hwnd)
                    if control is not None:
                        controls_to_stop.append(control)

            for hwnd, title in wanted.items():
                if hwnd in self._state:
                    continue
                generation = self._new_generation_locked()
                self._state[hwnd] = _State(
                    hwnd=hwnd,
                    title=title,
                    generation=generation,
                    last_check=0.0,
                    stable_active=False,
                    last_emit=0.0,
                    true_streak=0,
                    false_streak=0,
                )
                self._frames_seen[hwnd] = 0
                self._last_frame_ts[hwnd] = 0.0
                self._last_has_popup[hwnd] = False
                to_add.append((hwnd, title, generation))

        # Never wait for capture shutdown while holding the watcher lock.
        self._stop_controls(controls_to_stop)

        for hwnd, title, generation in to_add:
            try:
                cap = WindowsCapture(
                    cursor_capture=None,
                    draw_border=False,
                    monitor_index=None,
                    window_name=title,
                )
            except Exception as exc:
                with self._lock:
                    state = self._state.get(hwnd)
                    if state is not None and state.generation == generation:
                        self._detach_locked(hwnd)
                        self._failures[hwnd] = repr(exc)
                continue

            @cap.event  # type: ignore
            def on_frame_arrived(
                frame: Frame,
                capture_control: InternalCaptureControl,
                _hwnd=hwnd,
                _title=title,
                _generation=generation,
            ):
                del capture_control
                self._on_frame(_hwnd, _title, _generation, frame)

            @cap.event  # type: ignore
            def on_closed(
                _hwnd=hwnd,
                _generation=generation,
            ):
                self._on_closed(_hwnd, _generation)

            with self._lock:
                state = self._state.get(hwnd)
                if state is None or state.generation != generation:
                    continue
                self._captures[hwnd] = cap

            try:
                control = cap.start_free_threaded()
            except Exception as exc:
                with self._lock:
                    state = self._state.get(hwnd)
                    if state is not None and state.generation == generation:
                        self._detach_locked(hwnd)
                        self._failures[hwnd] = repr(exc)
                continue

            stop_immediately = False
            with self._lock:
                state = self._state.get(hwnd)
                if state is None or state.generation != generation:
                    stop_immediately = True
                else:
                    self._capture_controls[hwnd] = control
                    self._failures.pop(hwnd, None)
            if stop_immediately:
                self._stop_controls([control])

    def _on_closed(self, hwnd: int, generation: int) -> None:
        control: CaptureControl | None = None
        with self._lock:
            state = self._state.get(hwnd)
            if state is None or state.generation != generation:
                return
            control = self._detach_locked(hwnd)
        # A callback may be running from the same capture thread. Do not call
        # stop while holding the lock; best effort outside it is safe/idempotent.
        if control is not None:
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

    def is_current_event(self, event: PopupEvent) -> bool:
        with self._lock:
            state = self._state.get(int(event.hwnd))
            return bool(
                self._enabled
                and state is not None
                and state.generation == int(event.generation)
                and state.title == event.title
            )

    def _on_frame(self, hwnd: int, title: str, generation: int, frame: Frame) -> None:
        now = time.monotonic()

        with self._lock:
            state = self._state.get(hwnd)
            if (
                state is None
                or state.generation != generation
                or state.title != title
                or not self._enabled
            ):
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
            # Detection happened outside the lock; revalidate the same capture
            # identity before mutating state or emitting.
            state = self._state.get(hwnd)
            if (
                state is None
                or state.generation != generation
                or state.title != title
                or not self._enabled
            ):
                return

            self._frames_seen[hwnd] = self._frames_seen.get(hwnd, 0) + 1
            self._last_frame_ts[hwnd] = now
            self._last_has_popup[hwnd] = bool(has_popup)

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
                            hwnd=hwnd,
                            title=title,
                            ts=now,
                            generation=generation,
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
        """Return lightweight stats for debugging."""
        with self._lock:
            return {
                "enabled": bool(self._enabled),
                "targets": [
                    {
                        "hwnd": hwnd,
                        "title": state.title,
                        "generation": state.generation,
                    }
                    for hwnd, state in self._state.items()
                ],
                "frames_seen": dict(self._frames_seen),
                "last_frame_ts": dict(self._last_frame_ts),
                "last_has_popup": dict(self._last_has_popup),
                "failures": dict(self._failures),
            }
