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

    def test_same_title_new_hwnd_gets_a_distinct_capture_generation(self) -> None:
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
                watcher.set_enabled(True)
                watcher.update_targets(
                    [watcher_module.WatchedWindow(hwnd=42, title="Eniripsa")]
                )
                first_control = _FakeCapture.controls[-1]
                first_generation = watcher.get_stats()["targets"][0]["generation"]

                watcher.update_targets(
                    [watcher_module.WatchedWindow(hwnd=84, title="Eniripsa")]
                )

                stats = watcher.get_stats()
                self.assertTrue(first_control.stopped)
                self.assertEqual(stats["targets"][0]["hwnd"], 84)
                self.assertNotEqual(
                    stats["targets"][0]["generation"],
                    first_generation,
                )
                self.assertEqual(len(_FakeCapture.instances), 2)
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
            with patch.dict(
                sys.modules,
                {"numpy": fake_numpy, "windows_capture": fake_capture_module},
            ):
                watcher_module = importlib.import_module("dwm.retro_popup_watcher")
                watcher = watcher_module.RetroPopupWatcher(emit=lambda event: None)
                watcher.update_targets(
                    [watcher_module.WatchedWindow(hwnd=42, title="Old title")]
                )
                old_generation = watcher.get_stats()["targets"][0]["generation"]
                watcher.update_targets(
                    [watcher_module.WatchedWindow(hwnd=42, title="New title")]
                )
                replacement = watcher.get_stats()["targets"][0]

                watcher._on_closed(42, old_generation)

                current = watcher.get_stats()["targets"][0]
                self.assertEqual(current, replacement)
                self.assertEqual(current["title"], "New title")
        finally:
            for name in module_names:
                sys.modules.pop(name, None)

    def test_shutdown_stops_control_after_releasing_watcher_lock(self) -> None:
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
                watcher.update_targets(
                    [watcher_module.WatchedWindow(hwnd=42, title="Eniripsa")]
                )
                observed = []

                class LockCheckingControl:
                    def stop(self) -> None:
                        acquired = watcher._lock.acquire(blocking=False)
                        observed.append(acquired)
                        if acquired:
                            watcher._lock.release()

                watcher._capture_controls[42] = LockCheckingControl()
                watcher.shutdown()

                self.assertEqual(observed, [True])
                self.assertEqual(watcher.get_stats()["targets"], [])
        finally:
            for name in module_names:
                sys.modules.pop(name, None)


if __name__ == "__main__":
    unittest.main()
