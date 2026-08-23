from __future__ import annotations

import json
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from dwm.services.streamdeck_bridge import StreamDeckBridge


class StreamDeckBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.commands: list[tuple[str, dict[str, object]]] = []

        def dispatch(command: str, payload: dict[str, object]) -> dict[str, object]:
            self.commands.append((command, payload))
            return {"ok": True, "command": command}

        self.bridge = StreamDeckBridge(dispatch, port=0)
        self.bridge.update_snapshot(
            {
                "api_version": 1,
                "app_version": "2.16.3",
                "game_mode": "unity",
                "scan_revision": 3,
                "windows": [
                    {
                        "slot": 1,
                        "position": 1,
                        "hwnd": 101,
                        "name": "Korra",
                        "character_class": "Féca",
                        "active": True,
                        "ignored": False,
                    }
                ],
            }
        )
        self.bridge.start()
        self.base_url = f"http://127.0.0.1:{self.bridge.port}"

    def tearDown(self) -> None:
        self.bridge.stop()

    def request(self, path: str, *, method: str = "GET", body: object | None = None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {} if body is None else {"Content-Type": "application/json"}
        request = Request(self.base_url + path, data=data, headers=headers, method=method)
        with urlopen(request, timeout=2) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_status_returns_published_snapshot(self) -> None:
        self.assertIsNone(self.bridge.last_request_at)
        status, payload = self.request("/v1/status")

        self.assertEqual(status, 200)
        self.assertEqual(payload["windows"][0]["name"], "Korra")
        self.assertEqual(payload["windows"][0]["character_class"], "Féca")
        self.assertEqual(payload["scan_revision"], 3)
        self.assertTrue(payload["windows"][0]["active"])
        self.assertIsNotNone(self.bridge.last_request_at)

    def test_focus_dispatches_json_command(self) -> None:
        status, payload = self.request("/v1/focus", method="POST", body={"slot": 2})

        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(self.commands, [("focus", {"slot": 2})])

    def test_refresh_dispatches_command(self) -> None:
        status, payload = self.request("/v1/refresh", method="POST", body={})

        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(self.commands, [("refresh", {})])

    def test_show_dispatches_command(self) -> None:
        status, payload = self.request("/v1/show", method="POST", body={})

        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(self.commands, [("show", {})])

    def test_toggle_ignore_dispatches_command(self) -> None:
        status, payload = self.request("/v1/toggle-ignore", method="POST", body={})

        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(self.commands, [("toggle_ignore", {})])

    def test_reorder_dispatches_direction(self) -> None:
        status, payload = self.request("/v1/reorder", method="POST", body={"direction": "up"})

        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(self.commands, [("reorder", {"direction": "up"})])

    def test_next_attention_dispatches_command(self) -> None:
        status, payload = self.request("/v1/next-attention", method="POST", body={})

        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(self.commands, [("next_attention", {})])

    def test_post_rejects_non_json_content(self) -> None:
        request = Request(self.base_url + "/v1/refresh", data=b"{}", method="POST")

        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=2)

        self.assertEqual(caught.exception.code, 400)

    def test_browser_origin_is_rejected(self) -> None:
        request = Request(
            self.base_url + "/v1/refresh",
            data=b"{}",
            headers={"Content-Type": "application/json", "Origin": "https://example.test"},
            method="POST",
        )

        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=2)

        self.assertEqual(caught.exception.code, 403)


if __name__ == "__main__":
    unittest.main()
