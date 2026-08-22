from __future__ import annotations

import importlib
import sys
import types
import unittest
from unittest.mock import patch


class _FakeControl:
    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


class _FakeCapture:
    controls: list[_FakeControl] = []

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs

    def event(self, handler):
        return handler

    def start_free_threaded(self) -> _FakeControl:
        control = _FakeControl()
        self.controls.append(control)
        return control


class PopupWatcherLifecycleTests(unittest.TestCase):
    def test_capture_control_is_stopped_when_target_disappears(self) -> None:
        fake_capture_module = types.ModuleType("windows_capture")
        fake_capture_module.CaptureControl = _FakeControl
        fake_capture_module.Frame = object
        fake_capture_module.InternalCaptureControl = object
        fake_capture_module.WindowsCapture = _FakeCapture

        fake_numpy = types.ModuleType("numpy")
        _FakeCapture.controls.clear()

        module_names = ("dwm.retro_popup_watcher", "dwm.retro_popup_detector")
        for name in module_names:
            sys.modules.pop(name, None)

        try:
            with patch.dict(
                sys.modules,
                {"numpy": fake_numpy, "windows_capture": fake_capture_module},
            ):
                watcher_module = importlib.import_module("dwm.retro_popup_watcher")
                watcher = watcher_module.RetroPopupWatcher(emit=lambda event: None)
                watcher.update_targets([watcher_module.WatchedWindow(hwnd=42, title="Eniripsa")])
                control = _FakeCapture.controls[0]

                watcher.update_targets([])

                self.assertTrue(control.stopped)
        finally:
            for name in module_names:
                sys.modules.pop(name, None)


if __name__ == "__main__":
    unittest.main()
