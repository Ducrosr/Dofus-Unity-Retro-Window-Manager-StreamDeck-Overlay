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


class _BlockingControl(_FakeControl):
    def __init__(self, entered: threading.Event, release: threading.Event) -> None:
        super().__init__()
        self.entered = entered
        self.release = release

    def stop(self) -> None:
        self.entered.set()
        if not self.release.wait(2):
            raise AssertionError("control stop was not released")
        super().stop()


class _FakeCapture:
    controls: list[_FakeControl] = []
    instances: list["_FakeCapture"] = []
    control_factory = staticmethod(_FakeControl)

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.handlers: list[object] = []
        self.instances.append(self)

    def event(self, handler):
        self.handlers.append(handler)
        return handler

    def start_free_threaded(self) -> _FakeControl:
        control = self.control_factory()
        self.controls.append(control)
        return control


class _FakeFrame:
    class _Bgr:
        frame_buffer = object()

    def convert_to_bgr(self):
        return self._Bgr()


class PopupWatcherLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_capture_module = types.ModuleType("windows_capture")
        self.fake_capture_module.CaptureControl = _FakeControl
        self.fake_capture_module.Frame = object
        self.fake_capture_module.InternalCaptureControl = object
        self.fake_capture_module.WindowsCapture = _FakeCapture
        self.fake_numpy = types.ModuleType("numpy")
        _FakeCapture.controls.clear()
        _FakeCapture.instances.clear()
        _FakeCapture.control_factory = staticmethod(_FakeControl)

        self.module_names = ("dwm.retro_popup_watcher", "dwm.retro_popup_detector")
        for name in self.module_names:
            sys.modules.pop(name, None)

    def tearDown(self) -> None:
        for name in self.module_names:
            sys.modules.pop(name, None)

    def import_watcher(self):
        modules = {
            "numpy": self.fake_numpy,
            "windows_capture": self.fake_capture_module,
        }
        patcher = patch.dict(sys.modules, modules)
        patcher.start()
        self.addCleanup(patcher.stop)
        return importlib.import_module("dwm.retro_popup_watcher")

    def test_capture_control_is_stopped_when_target_disappears(self) -> None:
        watcher_module = self.import_watcher()
        watcher = watcher_module.RetroPopupWatcher(emit=lambda event: None)
        watcher.update_targets([watcher_module.WatchedWindow(hwnd=42, title="Eniripsa")])
        control = _FakeCapture.controls[0]

        watcher.update_targets([])

        self.assertTrue(control.stopped)

    def test_same_title_on_new_hwnd_gets_new_capture_generation(self) -> None:
        watcher_module = self.import_watcher()
        watcher = watcher_module.RetroPopupWatcher(emit=lambda event: None)
        watcher.set_enabled(True)
        watcher.update_targets([watcher_module.WatchedWindow(hwnd=42, title="Eniripsa")])
        first_stats = watcher.get_stats()
        first_generation = first_stats["targets"][0]["generation"]
        first_control = _FakeCapture.controls[0]

        watcher.update_targets([watcher_module.WatchedWindow(hwnd=84, title="Eniripsa")])

        second_stats = watcher.get_stats()
        self.assertTrue(first_control.stopped)
        self.assertEqual(second_stats["targets"][0]["hwnd"], 84)
        self.assertGreater(second_stats["targets"][0]["generation"], first_generation)
        self.assertEqual(len(_FakeCapture.instances), 2)

    def test_old_generation_close_callback_cannot_remove_replacement(self) -> None:
        watcher_module = self.import_watcher()
        watcher = watcher_module.RetroPopupWatcher(emit=lambda event: None)
        watcher.set_enabled(True)
        watcher.update_targets([watcher_module.WatchedWindow(hwnd=42, title="A")])
        old_capture = _FakeCapture.instances[0]
        old_close = old_capture.handlers[1]

        watcher.update_targets([watcher_module.WatchedWindow(hwnd=42, title="B")])
        current = watcher.get_stats()["targets"][0]
        old_close()

        after = watcher.get_stats()["targets"][0]
        self.assertEqual(after, current)
        self.assertEqual(after["title"], "B")

    def test_old_frame_is_rejected_after_target_generation_changes(self) -> None:
        watcher_module = self.import_watcher()
        emitted = []
        watcher = watcher_module.RetroPopupWatcher(
            emit=emitted.append,
            true_needed=1,
            cooldown_sec=0,
        )
        watcher.set_enabled(True)
        watcher.update_targets([watcher_module.WatchedWindow(hwnd=42, title="A")])
        old_capture = _FakeCapture.instances[0]
        old_frame = old_capture.handlers[0]

        watcher.update_targets([watcher_module.WatchedWindow(hwnd=42, title="B")])
        with patch.object(watcher_module, "detect_retro_modal_popup", return_value=True):
            old_frame(_FakeFrame(), None)

        self.assertEqual(emitted, [])

    def test_new_watcher_session_rejects_previous_session_event(self) -> None:
        watcher_module = self.import_watcher()
        first_events = []
        first = watcher_module.RetroPopupWatcher(
            emit=first_events.append,
            true_needed=1,
            cooldown_sec=0,
            generation_seed=1,
        )
        first.set_enabled(True)
        first.update_targets([watcher_module.WatchedWindow(hwnd=42, title="A")])
        first_generation = first.get_stats()["targets"][0]["generation"]
        old_event = watcher_module.PopupEvent(
            hwnd=42,
            title="A",
            ts=1.0,
            generation=first_generation,
        )

        second = watcher_module.RetroPopupWatcher(
            emit=lambda event: None,
            generation_seed=2,
        )
        second.set_enabled(True)
        second.update_targets([watcher_module.WatchedWindow(hwnd=42, title="A")])

        self.assertFalse(second.is_current_event(old_event))

    def test_shutdown_stops_blocking_control_outside_watcher_lock(self) -> None:
        watcher_module = self.import_watcher()
        entered = threading.Event()
        release = threading.Event()
        _FakeCapture.control_factory = staticmethod(
            lambda: _BlockingControl(entered, release)
        )
        watcher = watcher_module.RetroPopupWatcher(emit=lambda event: None)
        watcher.update_targets([watcher_module.WatchedWindow(hwnd=42, title="A")])

        shutdown_thread = threading.Thread(target=watcher.shutdown)
        shutdown_thread.start()
        self.assertTrue(entered.wait(1))

        # If stop() held the watcher lock this call would block until release.
        stats_done = threading.Event()

        def read_stats():
            watcher.get_stats()
            stats_done.set()

        stats_thread = threading.Thread(target=read_stats)
        stats_thread.start()
        self.assertTrue(stats_done.wait(0.5))

        release.set()
        shutdown_thread.join(2)
        stats_thread.join(2)
        self.assertFalse(shutdown_thread.is_alive())


if __name__ == "__main__":
    unittest.main()
