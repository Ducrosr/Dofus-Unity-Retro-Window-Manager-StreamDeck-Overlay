from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Callable, Dict, List

import numpy as np

from windows_capture import CaptureControl, Frame, InternalCaptureControl, WindowsCapture  # type: ignore

from .retro_popup_detector import detect_retro_modal_popup


@dataclass
class WatchedWindow:
    hwnd: int
    title: str


@dataclass
class PopupEvent:
    hwnd: int
    title: str
    ts: float


@dataclass
class _State:
    hwnd: int
    last_check: float
    stable_active: bool
    last_emit: float
    true_streak: int
    false_streak: int


class RetroPopupWatcher:
    """Detect modal popups in stacked Retro windows with Windows Graphics Capture.

    Key points:
    - No polling scans needed; frames arrive from WGC even if window is behind.
    - Uses hysteresis so we don't get stuck in a constant True state:
      - stable_active becomes True only after N consecutive True frames
      - stable_active becomes False only after M consecutive False frames
    """

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

        self._captures: Dict[str, WindowsCapture] = {}
        self._capture_controls: Dict[str, CaptureControl] = {}
        self._failures: Dict[str, str] = {}
        self._state: Dict[str, _State] = {}
        self._frames_seen: Dict[str, int] = {}
        self._last_frame_ts: Dict[str, float] = {}
        self._last_has_popup: Dict[str, bool] = {}

    def set_enabled(self, enabled: bool) -> None:
        with self._lock:
            self._enabled = bool(enabled)

    def update_targets(self, windows: List[WatchedWindow]) -> None:
        """
        Keep capture targets in sync with the managed windows list.
        Note: stopping & restarting WGC rapidly can be flaky; we stop only when target disappears.
        """
        with self._lock:
            wanted_titles = {w.title for w in windows}
            title_to_hwnd = {w.title: int(w.hwnd) for w in windows}

            # Remove old
            for title in list(self._captures.keys()):
                if title not in wanted_titles:
                    self._captures.pop(title, None)
                    control = self._capture_controls.pop(title, None)
                    if control is not None:
                        try:
                            control.stop()
                        except Exception:
                            pass
                    self._state.pop(title, None)
                    try:
                        self._failures.pop(title, None)
                        self._frames_seen.pop(title, None)
                        self._last_frame_ts.pop(title, None)
                        self._last_has_popup.pop(title, None)
                    except Exception:
                        pass

            # Add/update
            for title in wanted_titles:
                hwnd = title_to_hwnd[title]
                if title in self._captures:
                    st = self._state.get(title)
                    if st:
                        st.hwnd = hwnd
                    else:
                        self._state[title] = _State(hwnd=hwnd, last_check=0.0, stable_active=False,
                                                    last_emit=0.0, true_streak=0, false_streak=0)
                    continue

                try:
                    cap = WindowsCapture(
                        cursor_capture=None,
                        draw_border=False,
                        monitor_index=None,
                        window_name=title,
                    )
                except Exception as exc:
                    self._failures[title] = repr(exc)
                    continue

                self._captures[title] = cap
                self._failures.pop(title, None)

                self._frames_seen[title] = 0
                self._last_frame_ts[title] = 0.0
                self._last_has_popup[title] = False
                self._state[title] = _State(hwnd=hwnd, last_check=0.0, stable_active=False,
                                            last_emit=0.0, true_streak=0, false_streak=0)

                @cap.event  # type: ignore
                def on_frame_arrived(frame: Frame, capture_control: InternalCaptureControl, _title=title):
                    self._on_frame(_title, frame)

                @cap.event  # type: ignore
                def on_closed(_title=title):
                    with self._lock:
                        self._captures.pop(_title, None)
                        self._capture_controls.pop(_title, None)
                        self._state.pop(_title, None)
                        try:
                            self._failures.pop(_title, None)
                            self._frames_seen.pop(_title, None)
                            self._last_frame_ts.pop(_title, None)
                            self._last_has_popup.pop(_title, None)
                        except Exception:
                            pass

                try:
                    control = cap.start_free_threaded()
                    if title in self._captures:
                        self._capture_controls[title] = control
                    else:
                        # The target closed while the capture was starting.
                        control.stop()
                except Exception as exc:
                    # Remove partially-added capture and record failure
                    self._captures.pop(title, None)
                    self._capture_controls.pop(title, None)
                    self._failures[title] = repr(exc)
                    continue

    def shutdown(self) -> None:
        with self._lock:
            self._enabled = False
            for control in list(self._capture_controls.values()):
                try:
                    control.stop()
                except Exception:
                    pass
            self._captures.clear()
            self._capture_controls.clear()
            self._state.clear()
            self._frames_seen.clear()
            self._last_frame_ts.clear()
            self._last_has_popup.clear()
            self._failures.clear()

    def _on_frame(self, title: str, frame: Frame) -> None:
        now = time.monotonic()

        with self._lock:
            st = self._state.get(title)
            if not st:
                return

            if (now - st.last_check) < self._min_dt:
                return
            st.last_check = now

            if not self._enabled:
                return

        # Convert the captured frame to the detector's BGR numpy format.
        try:
            bgr_frame = frame.convert_to_bgr()
            img: np.ndarray = bgr_frame.frame_buffer
        except Exception:
            return

        with self._lock:
            try:
                self._frames_seen[title] = self._frames_seen.get(title, 0) + 1
                self._last_frame_ts[title] = now
            except Exception:
                pass
        try:
            has_popup = bool(detect_retro_modal_popup(img))
        except Exception:
            has_popup = False

        with self._lock:
            try:
                self._last_has_popup[title] = bool(has_popup)
            except Exception:
                pass
            st = self._state.get(title)
            if not st:
                return

            if has_popup:
                st.true_streak += 1
                st.false_streak = 0
            else:
                st.false_streak += 1
                st.true_streak = 0

            if not st.stable_active:
                if st.true_streak >= self._true_needed:
                    st.stable_active = True
                    st.true_streak = 0
                    if (now - st.last_emit) >= self._cooldown:
                        st.last_emit = now
                        try:
                            self._emit(PopupEvent(hwnd=st.hwnd, title=title, ts=now))
                        except Exception:
                            pass
            else:
                if st.false_streak >= self._false_needed:
                    st.stable_active = False
                    st.false_streak = 0

    def get_stats(self) -> dict:
        """Return lightweight stats for debugging."""
        with self._lock:
            return {
                "enabled": bool(self._enabled),
                "targets": list(self._captures.keys()),
                "frames_seen": dict(self._frames_seen),
                "last_frame_ts": dict(self._last_frame_ts),
                "last_has_popup": dict(self._last_has_popup),
                "failures": dict(self._failures),
            }
