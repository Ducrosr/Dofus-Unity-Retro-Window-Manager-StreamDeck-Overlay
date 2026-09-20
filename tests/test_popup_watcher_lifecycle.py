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
        self.handlers = []
        self.instances.append(self)

    def event(self, handler):
        self.handlers.append(handler)
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

    def test_same_title_with_new_hwnd_restarts_capture(self) -> None:
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
            with patch.dict(sys.modules, {"numpy": fake_numpy, "windows_capture": fake_capture_module}):
                watcher_module = importlib.import_module("dwm.retro_popup_watcher")
                watcher = watcher_module.RetroPopupWatcher(emit=lambda event: None)
                watcher.update_targets(
                    [watcher_module.WatchedWindow(hwnd=42, title="Eniripsa", generation=1)]
                )
                first_control = _FakeCapture.controls[0]

                watcher.update_targets(
                    [watcher_module.WatchedWindow(hwnd=84, title="Eniripsa", generation=2)]
                )

                self.assertTrue(first_control.stopped)
                self.assertEqual(len(_FakeCapture.controls), 2)
                self.assertIn(84, watcher._state)
                self.assertNotIn(42, watcher._state)
        finally:
            for name in module_names:
                sys.modules.pop(name, None)

    def test_stale_close_callback_cannot_remove_replacement_generation(self) -> None:
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
            with patch.dict(sys.modules, {"numpy": fake_numpy, "windows_capture": fake_capture_module}):
                watcher_module = importlib.import_module("dwm.retro_popup_watcher")
                watcher = watcher_module.RetroPopupWatcher(emit=lambda event: None)
                watcher.update_targets(
                    [watcher_module.WatchedWindow(hwnd=42, title="Old", generation=1)]
                )
                old_closed = _FakeCapture.instances[0].handlers[1]

                watcher.update_targets(
                    [watcher_module.WatchedWindow(hwnd=42, title="New", generation=2)]
                )
                old_closed()

                self.assertIn(42, watcher._state)
                self.assertEqual(watcher._state[42].title, "New")
                self.assertEqual(watcher._state[42].generation, 2)
        finally:
            for name in module_names:
                sys.modules.pop(name, None)

    def test_shutdown_stops_control_outside_watcher_lock(self) -> None:
        callback_completed = threading.Event()
        watcher_holder = {}

        class ReentrantControl(_FakeControl):
            stop_observed_unlocked = False

            def stop(self) -> None:
                def inspect() -> None:
                    watcher_holder["watcher"].get_stats()
                    callback_completed.set()

                thread = threading.Thread(target=inspect)
                thread.start()
                type(self).stop_observed_unlocked = callback_completed.wait(0.5)
                thread.join(timeout=0.5)
                super().stop()

        class ReentrantCapture(_FakeCapture):
            controls: list[ReentrantControl] = []
            instances: list["ReentrantCapture"] = []

            def start_free_threaded(self):
                control = ReentrantControl()
                self.controls.append(control)
                return control

        fake_capture_module = types.ModuleType("windows_capture")
        fake_capture_module.CaptureControl = ReentrantControl
        fake_capture_module.Frame = object
        fake_capture_module.InternalCaptureControl = object
        fake_capture_module.WindowsCapture = ReentrantCapture
        fake_numpy = types.ModuleType("numpy")
        ReentrantCapture.controls.clear()
        ReentrantCapture.instances.clear()

        module_names = ("dwm.retro_popup_watcher", "dwm.retro_popup_detector")
        for name in module_names:
            sys.modules.pop(name, None)
        try:
            with patch.dict(sys.modules, {"numpy": fake_numpy, "windows_capture": fake_capture_module}):
                watcher_module = importlib.import_module("dwm.retro_popup_watcher")
                watcher = watcher_module.RetroPopupWatcher(emit=lambda event: None)
                watcher_holder["watcher"] = watcher
                watcher.update_targets([watcher_module.WatchedWindow(hwnd=42, title="Eniripsa")])
                control = ReentrantCapture.controls[0]

                watcher.shutdown()

                self.assertTrue(control.stopped)
                self.assertTrue(ReentrantControl.stop_observed_unlocked)
        finally:
            for name in module_names:
                sys.modules.pop(name, None)



if __name__ == "__main__":
    unittest.main()
