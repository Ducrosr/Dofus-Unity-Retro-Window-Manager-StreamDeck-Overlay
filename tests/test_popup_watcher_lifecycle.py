from __future__ import annotations

import importlib
import sys
import threading
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
    instances: list["_FakeCapture"] = []

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.handlers: dict[str, object] = {}
        self.instances.append(self)

    def event(self, handler):
        self.handlers[handler.__name__] = handler
        return handler

    def start_free_threaded(self) -> _FakeControl:
        control = _FakeControl()
        self.controls.append(control)
        return control


class _WaitingControl:
    def __init__(self, closed_callback) -> None:
        self.closed_callback = closed_callback
        self.callback_completed = False

    def stop(self) -> None:
        completed = threading.Event()

        def callback() -> None:
            self.closed_callback()
            self.callback_completed = True
            completed.set()

        thread = threading.Thread(target=callback)
        thread.start()
        thread.join(timeout=0.5)


class _WaitingCapture(_FakeCapture):
    controls: list[_WaitingControl] = []
    instances: list["_WaitingCapture"] = []

    def start_free_threaded(self) -> _WaitingControl:
        control = _WaitingControl(self.handlers["on_closed"])
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
        _FakeCapture.instances.clear()

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

    def test_same_title_new_hwnd_gets_new_generation_and_old_close_cannot_remove_it(self) -> None:
        fake_capture_module = types.ModuleType("windows_capture")
        fake_capture_module.CaptureControl = _FakeControl
        fake_capture_module.Frame = object
        fake_capture_module.InternalCaptureControl = object
        fake_capture_module.WindowsCapture = _FakeCapture
        fake_numpy = types.ModuleType("numpy")
        _FakeCapture.controls.clear()
        _FakeCapture.instances.clear()

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
                old_capture = _FakeCapture.instances[-1]

                watcher.update_targets([watcher_module.WatchedWindow(hwnd=84, title="Eniripsa")])

                self.assertTrue(_FakeCapture.controls[0].stopped)
                self.assertEqual(len(_FakeCapture.controls), 2)
                old_capture.handlers["on_closed"]()
                targets = watcher.get_stats()["targets"]
                self.assertEqual(len(targets), 1)
                self.assertIn("#84@", targets[0])
        finally:
            for name in module_names:
                sys.modules.pop(name, None)

    def test_shutdown_stops_controls_outside_lock_so_closed_callback_can_finish(self) -> None:
        fake_capture_module = types.ModuleType("windows_capture")
        fake_capture_module.CaptureControl = _WaitingControl
        fake_capture_module.Frame = object
        fake_capture_module.InternalCaptureControl = object
        fake_capture_module.WindowsCapture = _WaitingCapture
        fake_numpy = types.ModuleType("numpy")
        _WaitingCapture.controls.clear()
        _WaitingCapture.instances.clear()

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
                control = _WaitingCapture.controls[0]

                watcher.shutdown()

                self.assertTrue(control.callback_completed)
        finally:
            for name in module_names:
                sys.modules.pop(name, None)


if __name__ == "__main__":
    unittest.main()
