from __future__ import annotations

import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from dwm.services.obs_active_capture import (
    ADVSS_GAME_VARIABLE_NAME,
    ADVSS_SET_VARIABLES_REQUEST,
    ADVSS_VENDOR_NAME,
    OBSActiveCaptureBridge,
    OBSActiveCaptureConfig,
    OVERLAY_SOURCE_NAME,
    POPUP_COLOR_KEY_FILTER_NAME,
    POPUP_OPACITY_FILTER_NAME,
    POPUP_SOURCE_NAME,
    VISIBILITY_FILTER_NAME,
    advanced_scene_switcher_game_value,
    fit_window_to_canvas,
    project_window_over_reference,
    probe_obs_connection,
)
from dwm.services.window_telemetry import RectSnapshot, WindowTelemetry


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
        if request == "GetVideoSettings":
            return {"baseWidth": 1920, "baseHeight": 1080}
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
        if request == "GetSceneItemList":
            scene = str(payload["sceneName"])
            return {
                "sceneItems": [
                    {
                        "sceneItemId": item_id,
                        "sourceName": source_name,
                    }
                    for (item_scene, source_name), item_id in self.scene_items.items()
                    if item_scene == scene
                ]
            }
        if request == "SetSceneItemIndex":
            return {}
        if request == "SetSceneItemTransform":
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
        if request == "SetSourceFilterIndex":
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


def _interface_window(index: int, title: str) -> WindowTelemetry:
    hwnd = 900 + index
    return WindowTelemetry(
        hwnd=hwnd,
        session_id=f"dwm:{index}:{hwnd}",
        game_mode="dwm",
        title=title,
        window_class="TkTopLevel",
        pseudo="",
        character_class="",
        pid=5000,
        process_path=r"C:\Tools\DofusWindowManager.exe",
        process_name="DofusWindowManager.exe",
        process_created_100ns=123456789,
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


class OBSProjectionTests(unittest.TestCase):
    def test_fit_1440p_game_into_1080p_canvas(self):
        game = WindowTelemetry(
            hwnd=1,
            session_id="1",
            game_mode="unity",
            title="Dofus",
            window_class="UnityWndClass",
            pseudo="",
            character_class="",
            client_rect_screen=RectSnapshot(1920, 0, 4480, 1440),
        )

        transform = fit_window_to_canvas(game, 1920, 1080)

        self.assertIsNotNone(transform)
        self.assertAlmostEqual(transform.position_x, 0.0)
        self.assertAlmostEqual(transform.position_y, 0.0)
        self.assertAlmostEqual(transform.scale_x, 0.75)
        self.assertAlmostEqual(transform.scale_y, 0.75)

    def test_overlay_is_projected_relative_to_active_game_client(self):
        game = WindowTelemetry(
            hwnd=1,
            session_id="1",
            game_mode="unity",
            title="Dofus",
            window_class="UnityWndClass",
            pseudo="",
            character_class="",
            client_rect_screen=RectSnapshot(1920, 0, 4480, 1440),
        )
        overlay = WindowTelemetry(
            hwnd=2,
            session_id="2",
            game_mode="dwm",
            title="Dofus Window Manager — Overlay",
            window_class="TkTopLevel",
            pseudo="",
            character_class="",
            client_rect_screen=RectSnapshot(2180, 160, 2480, 760),
        )

        transform = project_window_over_reference(overlay, game, 1920, 1080)

        self.assertIsNotNone(transform)
        self.assertAlmostEqual(transform.position_x, 195.0)
        self.assertAlmostEqual(transform.position_y, 120.0)
        self.assertAlmostEqual(transform.scale_x, 0.75)
        self.assertAlmostEqual(transform.scale_y, 0.75)


class AdvancedSceneSwitcherGameTests(unittest.TestCase):
    def test_game_values_match_expected_stream_variables(self):
        self.assertEqual(advanced_scene_switcher_game_value("unity"), "Dofus Unity")
        self.assertEqual(advanced_scene_switcher_game_value("retro"), "Dofus Retro")

    def test_bridge_sets_game_variable_and_updates_it_on_mode_switch(self):
        _FakeReqClient.reset()
        fake_obs = SimpleNamespace(ReqClient=_FakeReqClient)

        with (
            patch("dwm.services.obs_active_capture._obs", fake_obs),
            patch.object(
                OBSActiveCaptureBridge,
                "_find_interface_window",
                return_value=None,
            ),
        ):
            bridge = OBSActiveCaptureBridge(OBSActiveCaptureConfig(enabled=True))
            try:
                bridge.set_game_mode("retro")
                bridge.sync_windows([], active_hwnd=None)
                self.assertTrue(
                    _wait_until(
                        lambda: any(
                            request == "CallVendorRequest"
                            for request, _payload in _FakeReqClient.calls
                        )
                    )
                )

                first_payload = next(
                    payload
                    for request, payload in _FakeReqClient.calls
                    if request == "CallVendorRequest"
                )
                self.assertEqual(first_payload["vendorName"], ADVSS_VENDOR_NAME)
                self.assertEqual(
                    first_payload["requestType"],
                    ADVSS_SET_VARIABLES_REQUEST,
                )
                self.assertEqual(
                    first_payload["requestData"]["variables"],
                    [
                        {
                            "name": ADVSS_GAME_VARIABLE_NAME,
                            "value": "Dofus Retro",
                        }
                    ],
                )

                _FakeReqClient.calls = []
                bridge.set_game_mode("unity")
                self.assertTrue(
                    _wait_until(
                        lambda: any(
                            request == "CallVendorRequest"
                            and payload
                            and payload["requestData"]["variables"][0]["value"]
                            == "Dofus Unity"
                            for request, payload in _FakeReqClient.calls
                        )
                    )
                )
            finally:
                bridge.stop()


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

    def test_overlay_and_popup_are_created_above_dynamic_dofus_captures(self):
        fake_obs = SimpleNamespace(ReqClient=_FakeReqClient)
        overlay = _interface_window(1, "Dofus Window Manager — Overlay")
        popup = _interface_window(2, "Dofus Window Manager — Focus Popup")

        def interface_lookup(title: str):
            if title.endswith("Overlay"):
                return overlay
            if title.endswith("Focus Popup"):
                return popup
            return None

        with (
            patch("dwm.services.obs_active_capture._obs", fake_obs),
            patch.object(
                OBSActiveCaptureBridge,
                "_find_interface_window",
                side_effect=interface_lookup,
            ),
        ):
            bridge = OBSActiveCaptureBridge(
                OBSActiveCaptureConfig(enabled=True, popup_opacity=0.71)
            )
            try:
                bridge.sync_windows([_window(1), _window(2)], active_hwnd=102)
                self.assertTrue(
                    _wait_until(
                        lambda: OVERLAY_SOURCE_NAME in _FakeReqClient.inputs
                        and POPUP_SOURCE_NAME in _FakeReqClient.inputs
                        and POPUP_SOURCE_NAME in _FakeReqClient.filters
                    )
                )
            finally:
                bridge.stop()

        self.assertIn(OVERLAY_SOURCE_NAME, _FakeReqClient.inputs)
        self.assertIn(POPUP_SOURCE_NAME, _FakeReqClient.inputs)
        self.assertIn(
            POPUP_COLOR_KEY_FILTER_NAME,
            _FakeReqClient.filters[POPUP_SOURCE_NAME],
        )
        self.assertIn(
            POPUP_OPACITY_FILTER_NAME,
            _FakeReqClient.filters[POPUP_SOURCE_NAME],
        )
        self.assertEqual(
            _FakeReqClient.filters[POPUP_SOURCE_NAME][POPUP_OPACITY_FILTER_NAME][
                "settings"
            ]["opacity"],
            0.71,
        )

        order_calls = [
            payload
            for request, payload in _FakeReqClient.calls
            if request == "SetSceneItemIndex"
        ]
        self.assertGreaterEqual(len(order_calls), 2)
        overlay_item = _FakeReqClient.scene_items[
            ("[DWM] Dofus Active", OVERLAY_SOURCE_NAME)
        ]
        popup_item = _FakeReqClient.scene_items[
            ("[DWM] Dofus Active", POPUP_SOURCE_NAME)
        ]
        self.assertEqual(order_calls[-2]["sceneItemId"], overlay_item)
        self.assertEqual(order_calls[-1]["sceneItemId"], popup_item)
        self.assertEqual(
            order_calls[-2]["sceneItemIndex"],
            order_calls[-1]["sceneItemIndex"],
        )

    def test_new_dynamic_capture_reasserts_interface_layers_on_top(self):
        fake_obs = SimpleNamespace(ReqClient=_FakeReqClient)
        overlay = _interface_window(1, "Dofus Window Manager — Overlay")
        popup = _interface_window(2, "Dofus Window Manager — Focus Popup")

        def interface_lookup(title: str):
            return overlay if title.endswith("Overlay") else popup

        with (
            patch("dwm.services.obs_active_capture._obs", fake_obs),
            patch.object(
                OBSActiveCaptureBridge,
                "_find_interface_window",
                side_effect=interface_lookup,
            ),
        ):
            bridge = OBSActiveCaptureBridge(OBSActiveCaptureConfig(enabled=True))
            try:
                bridge.sync_windows([_window(1)], active_hwnd=101)
                self.assertTrue(
                    _wait_until(lambda: POPUP_SOURCE_NAME in _FakeReqClient.inputs)
                )
                _FakeReqClient.calls = []

                bridge.sync_windows([_window(1), _window(2)], active_hwnd=102)
                self.assertTrue(
                    _wait_until(
                        lambda: any(
                            request == "CreateInput"
                            and payload
                            and payload.get("inputName") == "[DWM] Dofus Capture 02"
                            for request, payload in _FakeReqClient.calls
                        )
                        and len(
                            [
                                call
                                for call in _FakeReqClient.calls
                                if call[0] == "SetSceneItemIndex"
                            ]
                        )
                        >= 2
                    )
                )
            finally:
                bridge.stop()

        order_calls = [
            payload
            for request, payload in _FakeReqClient.calls
            if request == "SetSceneItemIndex"
        ]
        overlay_item = _FakeReqClient.scene_items[
            ("[DWM] Dofus Active", OVERLAY_SOURCE_NAME)
        ]
        popup_item = _FakeReqClient.scene_items[
            ("[DWM] Dofus Active", POPUP_SOURCE_NAME)
        ]
        self.assertEqual(order_calls[-2]["sceneItemId"], overlay_item)
        self.assertEqual(order_calls[-1]["sceneItemId"], popup_item)

    def test_shutdown_hides_overlay_and_popup_but_keeps_game_capture_enabled(self):
        fake_obs = SimpleNamespace(ReqClient=_FakeReqClient)
        overlay = _interface_window(1, "Dofus Window Manager — Overlay")
        popup = _interface_window(2, "Dofus Window Manager — Focus Popup")

        def interface_lookup(title: str):
            if title.endswith("Overlay"):
                return overlay
            if title.endswith("Focus Popup"):
                return popup
            return None

        with (
            patch("dwm.services.obs_active_capture._obs", fake_obs),
            patch.object(
                OBSActiveCaptureBridge,
                "_find_interface_window",
                side_effect=interface_lookup,
            ),
        ):
            bridge = OBSActiveCaptureBridge(OBSActiveCaptureConfig(enabled=True))
            bridge.sync_windows([_window(1)], active_hwnd=101)
            self.assertTrue(
                _wait_until(
                    lambda: OVERLAY_SOURCE_NAME in _FakeReqClient.inputs
                    and POPUP_SOURCE_NAME in _FakeReqClient.inputs
                )
            )

            game_item = _FakeReqClient.scene_items[
                ("[DWM] Dofus Active", "[DWM] Dofus Capture 01")
            ]
            overlay_item = _FakeReqClient.scene_items[
                ("[DWM] Dofus Active", OVERLAY_SOURCE_NAME)
            ]
            popup_item = _FakeReqClient.scene_items[
                ("[DWM] Dofus Active", POPUP_SOURCE_NAME)
            ]

            bridge.stop()

        self.assertTrue(_FakeReqClient.enabled[game_item])
        self.assertFalse(_FakeReqClient.enabled[overlay_item])
        self.assertFalse(_FakeReqClient.enabled[popup_item])

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
