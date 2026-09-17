from __future__ import annotations

import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from dwm.services.obs_active_capture import (
    GAME_CAPTURE_HOTKEY_NAME,
    OBSActiveCaptureBridge,
    OBSActiveCaptureConfig,
    probe_obs_connection,
)


class _FakeReqClient:
    calls: list[tuple[str, object]] = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def send(self, request, data=None, raw=False):
        self.calls.append((request, data))
        if request == "GetVersion":
            return {"obsVersion": "32.0.0"}
        return {}


class OBSActiveCaptureTests(unittest.TestCase):
    def setUp(self):
        _FakeReqClient.calls = []

    def test_config_normalizes_localhost_port_and_source(self):
        config = OBSActiveCaptureConfig(
            enabled=True,
            host="example.com",
            port=99999,
            source_name="",
        ).normalized()

        self.assertEqual(config.host, "127.0.0.1")
        self.assertEqual(config.port, 65535)
        self.assertEqual(config.source_name, "[Dofus] Client actif")

    def test_probe_only_reads_obs_version(self):
        fake_obs = SimpleNamespace(ReqClient=_FakeReqClient)
        with patch("dwm.services.obs_active_capture._obs", fake_obs):
            ok, message = probe_obs_connection(
                OBSActiveCaptureConfig(port=4455, password="pw")
            )

        self.assertTrue(ok)
        self.assertIn("OBS WebSocket connecté", message)
        self.assertEqual(_FakeReqClient.calls, [("GetVersion", None)])

    def test_trigger_uses_source_context_and_game_capture_hotkey(self):
        fake_obs = SimpleNamespace(ReqClient=_FakeReqClient)
        with patch("dwm.services.obs_active_capture._obs", fake_obs):
            bridge = OBSActiveCaptureBridge(
                OBSActiveCaptureConfig(
                    enabled=True,
                    port=4455,
                    password="pw",
                    source_name="[Dofus] Client actif",
                )
            )
            try:
                self.assertTrue(bridge.trigger_capture())
                deadline = time.monotonic() + 1.0
                while not _FakeReqClient.calls and time.monotonic() < deadline:
                    time.sleep(0.01)
            finally:
                bridge.stop()

        self.assertEqual(
            _FakeReqClient.calls,
            [
                (
                    "TriggerHotkeyByName",
                    {
                        "hotkeyName": GAME_CAPTURE_HOTKEY_NAME,
                        "contextName": "[Dofus] Client actif",
                    },
                )
            ],
        )

    def test_disabled_bridge_does_not_queue_capture(self):
        fake_obs = SimpleNamespace(ReqClient=_FakeReqClient)
        with patch("dwm.services.obs_active_capture._obs", fake_obs):
            bridge = OBSActiveCaptureBridge(OBSActiveCaptureConfig(enabled=False))
            try:
                self.assertFalse(bridge.trigger_capture())
                time.sleep(0.05)
            finally:
                bridge.stop()

        self.assertEqual(_FakeReqClient.calls, [])


if __name__ == "__main__":
    unittest.main()
