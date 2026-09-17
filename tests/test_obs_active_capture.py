from __future__ import annotations

import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from dwm.services.obs_active_capture import (
    OBSActiveCaptureBridge,
    OBSActiveCaptureConfig,
    VISIBILITY_FILTER_NAME,
    probe_obs_connection,
)
from dwm.services.window_telemetry import WindowTelemetry


class _FakeReqClient:
    calls: list[tuple[str, object]] = []
    scenes: set[str] = set()
    inputs: dict[str, dict[str, object]] = {}
    scene_items: dict[tuple[str, str], int] = {}
    enabled: dict[int, bool] = {}
    filters: dict[str, dict[str, dict[str, object]]] = {}
    next_item_id = 1

    @classmethod
    def reset(cls) -> None:
        cls.calls = []
        cls.scenes = set()
        cls.inputs = {}
        cls.scene_items = {}
        cls.enabled = {}
        cls.filters = {}
        cls.next_item_id = 1

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def send(self, request, data=None, raw=False):
        payload = dict(data or {})
        self.calls.append((request, data))

        if request == "GetVersion":
            return {"obsVersion": "32.0.0"}
        if request == "GetSceneList":
            return {"scenes": [{"sceneName": name} for name in sorted(self.scenes)]}
        if request == "CreateScene":
            self.scenes.add(str(payload["sceneName"]))
            return {}
        if request == "GetInputList":
            requested_kind = payload.get("inputKind")
            return {
                "inputs": [
                    {"inputName": name, "inputKind": value["kind"]}
                    for name, value in sorted(self.inputs.items())
                    if not requested_kind or value["kind"] == requested_kind
                ]
            }
        if request == "CreateInput":
            name = str(payload["inputName"])
            scene = str(payload["sceneName"])
            self.inputs[name] = {
                "kind": str(payload["inputKind"]),
                "settings": dict(payload.get("inputSettings") or {}),
            }
            item_id = self.next_item_id
            self.__class__.next_item_id += 1
            self.scene_items[(scene, name)] = item_id
            self.enabled[item_id] = bool(payload.get("sceneItemEnabled", True))
            return {"sceneItemId": item_id, "inputUuid": f"uuid-{item_id}"}
        if request == "GetSceneItemId":
            key = (str(payload["sceneName"]), str(payload["sourceName"]))
            if key not in self.scene_items:
                raise RuntimeError("scene item missing")
            return {"sceneItemId": self.scene_items[key]}
        if request == "CreateSceneItem":
            key = (str(payload["sceneName"]), str(payload["sourceName"]))
            item_id = self.next_item_id
            self.__class__.next_item_id += 1
            self.scene_items[key] = item_id
            self.enabled[item_id] = bool(payload.get("sceneItemEnabled", True))
            return {"sceneItemId": item_id}
        if request == "SetInputSettings":
            name = str(payload["inputName"])
            self.inputs[name]["settings"].update(dict(payload["inputSettings"]))
            return {}
        if request == "SetSceneItemEnabled":
            item_id = int(payload["sceneItemId"])
            self.enabled[item_id] = bool(payload["sceneItemEnabled"])
            return {}
        if request == "GetSourceFilterList":
            source = str(payload["sourceName"])
            return {
                "filters": [
                    {
                        "filterName": name,
                        "filterKind": value["kind"],
                        "filterEnabled": value["enabled"],
                        "filterSettings": dict(value["settings"]),
                    }
                    for name, value in self.filters.get(source, {}).items()
                ]
            }
        if request == "CreateSourceFilter":
            source = str(payload["sourceName"])
            name = str(payload["filterName"])
            self.filters.setdefault(source, {})[name] = {
                "kind": str(payload["filterKind"]),
                "enabled": True,
                "settings": dict(payload.get("filterSettings") or {}),
            }
            return {}
        if request == "SetSourceFilterSettings":
            source = str(payload["sourceName"])
            name = str(payload["filterName"])
            self.filters[source][name]["settings"].update(
                dict(payload.get("filterSettings") or {})
            )
            return {}
        if request == "SetSourceFilterEnabled":
            source = str(payload["sourceName"])
            name = str(payload["filterName"])
            self.filters[source][name]["enabled"] = bool(payload["filterEnabled"])
            return {}

        return {}


def _window(index: int) -> WindowTelemetry:
    hwnd = 100 + index
    return WindowTelemetry(
        hwnd=hwnd,
        session_id=f"{1000 + index}:{2000 + index}:{hwnd}",
        game_mode="unity",
        title=f"Character{index} - Cra - Dofus",
        window_class="UnityWndClass",
        pseudo=f"Character{index}",
        character_class="Crâ",
        pid=1000 + index,
        thread_id=3000 + index,
        process_path=r"C:\Games\Dofus\Dofus.exe",
        process_name="Dofus.exe",
        process_created_100ns=2000 + index,
    )


def _wait_until(predicate, timeout: float = 2.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return bool(predicate())


def _opacity(source_name: str) -> float:
    return float(
        _FakeReqClient.filters[source_name][VISIBILITY_FILTER_NAME]["settings"]["opacity"]
    )


class OBSActiveCaptureTests(unittest.TestCase):
    def setUp(self):
        _FakeReqClient.reset()

    def test_config_normalizes_localhost_port_scene_and_prefix(self):
        config = OBSActiveCaptureConfig(
            enabled=True,
            host="example.com",
            port=99999,
            scene_name="",
            source_prefix="",
        ).normalized()

        self.assertEqual(config.host, "127.0.0.1")
        self.assertEqual(config.port, 65535)
        self.assertEqual(config.scene_name, "[DWM] Dofus Active")
        self.assertEqual(config.source_prefix, "[DWM] Dofus Capture")

    def test_probe_only_reads_obs_version(self):
        fake_obs = SimpleNamespace(ReqClient=_FakeReqClient)
        with patch("dwm.services.obs_active_capture._obs", fake_obs):
            ok, message = probe_obs_connection(
                OBSActiveCaptureConfig(port=4455, password="pw")
            )

        self.assertTrue(ok)
        self.assertIn("OBS WebSocket connecté", message)
        self.assertEqual(_FakeReqClient.calls, [("GetVersion", None)])

    def test_pool_grows_beyond_eight_clients_and_keeps_all_captures_warm(self):
        fake_obs = SimpleNamespace(ReqClient=_FakeReqClient)
        windows = [_window(index) for index in range(1, 10)]

        with patch("dwm.services.obs_active_capture._obs", fake_obs):
            bridge = OBSActiveCaptureBridge(
                OBSActiveCaptureConfig(enabled=True, password="pw")
            )
            try:
                bridge.sync_windows(windows, active_hwnd=109)
                self.assertTrue(
                    _wait_until(
                        lambda: len(
                            [
                                call
                                for call in _FakeReqClient.calls
                                if call[0] == "CreateInput"
                            ]
                        )
                        == 9
                        and len(_FakeReqClient.filters) == 9
                    )
                )
            finally:
                bridge.stop()

        expected_names = {
            f"[DWM] Dofus Capture {slot:02d}" for slot in range(1, 10)
        }
        self.assertEqual(set(_FakeReqClient.inputs), expected_names)
        self.assertIn("[DWM] Dofus Active", _FakeReqClient.scenes)

        # Every currently assigned scene item stays enabled so OBS keeps the WGC
        # sessions initialized; opacity decides which client reaches the output.
        enabled_items = {
            item_id for item_id, enabled in _FakeReqClient.enabled.items() if enabled
        }
        self.assertEqual(enabled_items, set(_FakeReqClient.scene_items.values()))

        for slot in range(1, 9):
            self.assertEqual(_opacity(f"[DWM] Dofus Capture {slot:02d}"), 0.0)
        self.assertEqual(_opacity("[DWM] Dofus Capture 09"), 1.0)

    def test_focus_swap_only_changes_opacity_for_initialized_pool(self):
        fake_obs = SimpleNamespace(ReqClient=_FakeReqClient)
        windows = [_window(index) for index in range(1, 4)]

        with patch("dwm.services.obs_active_capture._obs", fake_obs):
            bridge = OBSActiveCaptureBridge(OBSActiveCaptureConfig(enabled=True))
            try:
                bridge.sync_windows(windows, active_hwnd=103)
                self.assertTrue(
                    _wait_until(
                        lambda: len(
                            [call for call in _FakeReqClient.calls if call[0] == "CreateInput"]
                        )
                        == 3
                        and len(_FakeReqClient.filters) == 3
                    )
                )
                _FakeReqClient.calls = []

                bridge.set_active_window(101)
                self.assertTrue(
                    _wait_until(
                        lambda: len(
                            [
                                call
                                for call in _FakeReqClient.calls
                                if call[0] == "SetSourceFilterSettings"
                            ]
                        )
                        >= 2
                    )
                )
            finally:
                bridge.stop()

        requests = [call[0] for call in _FakeReqClient.calls]
        self.assertNotIn("CreateInput", requests)
        self.assertNotIn("SetInputSettings", requests)
        self.assertNotIn("SetSceneItemEnabled", requests)
        self.assertEqual(_opacity("[DWM] Dofus Capture 01"), 1.0)
        self.assertEqual(_opacity("[DWM] Dofus Capture 03"), 0.0)

        # All three captures are still active/showing after the swap.
        enabled_items = {
            item_id for item_id, enabled in _FakeReqClient.enabled.items() if enabled
        }
        self.assertEqual(enabled_items, set(_FakeReqClient.scene_items.values()))

    def test_closed_client_is_made_transparent_then_deactivated(self):
        fake_obs = SimpleNamespace(ReqClient=_FakeReqClient)
        windows = [_window(index) for index in range(1, 3)]

        with patch("dwm.services.obs_active_capture._obs", fake_obs):
            bridge = OBSActiveCaptureBridge(OBSActiveCaptureConfig(enabled=True))
            try:
                bridge.sync_windows(windows, active_hwnd=102)
                self.assertTrue(
                    _wait_until(lambda: len(_FakeReqClient.filters) == 2)
                )
                bridge.sync_windows([windows[0]], active_hwnd=101)
                second_item = _FakeReqClient.scene_items[
                    ("[DWM] Dofus Active", "[DWM] Dofus Capture 02")
                ]
                self.assertTrue(
                    _wait_until(lambda: not _FakeReqClient.enabled[second_item])
                )
            finally:
                bridge.stop()

        self.assertEqual(_opacity("[DWM] Dofus Capture 02"), 0.0)

    def test_disabled_bridge_does_not_touch_obs(self):
        fake_obs = SimpleNamespace(ReqClient=_FakeReqClient)
        with patch("dwm.services.obs_active_capture._obs", fake_obs):
            bridge = OBSActiveCaptureBridge(OBSActiveCaptureConfig(enabled=False))
            try:
                bridge.sync_windows([_window(1)], active_hwnd=101)
                time.sleep(0.05)
            finally:
                bridge.stop()

        self.assertEqual(_FakeReqClient.calls, [])


if __name__ == "__main__":
    unittest.main()
