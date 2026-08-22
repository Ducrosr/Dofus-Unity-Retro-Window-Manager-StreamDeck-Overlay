from __future__ import annotations

import copy
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable


CommandDispatcher = Callable[[str, dict[str, object]], dict[str, object]]


class _LocalThreadingHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class StreamDeckBridge:
    """Small loopback-only HTTP bridge consumed by the Stream Deck plugin."""

    def __init__(
        self,
        dispatch: CommandDispatcher,
        *,
        host: str = "127.0.0.1",
        port: int = 32145,
        max_body_bytes: int = 4096,
    ) -> None:
        if host != "127.0.0.1":
            raise ValueError("Le pont Stream Deck doit rester lié à 127.0.0.1.")

        self._dispatch = dispatch
        self._host = host
        self._requested_port = int(port)
        self._max_body_bytes = int(max_body_bytes)
        self._snapshot_lock = threading.Lock()
        self._snapshot: dict[str, object] = {
            "api_version": 1,
            "app_version": "",
            "game_mode": "unity",
            "scan_revision": 0,
            "windows": [],
        }
        self._server: _LocalThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._last_request_at: float | None = None

    @property
    def port(self) -> int:
        server = self._server
        if server is None:
            return self._requested_port
        return int(server.server_address[1])

    @property
    def is_running(self) -> bool:
        thread = self._thread
        return bool(thread and thread.is_alive())

    @property
    def last_request_at(self) -> float | None:
        with self._snapshot_lock:
            return self._last_request_at

    def _record_request(self) -> None:
        with self._snapshot_lock:
            self._last_request_at = time.time()

    def update_snapshot(self, snapshot: dict[str, object]) -> None:
        with self._snapshot_lock:
            self._snapshot = copy.deepcopy(snapshot)

    def get_snapshot(self) -> dict[str, object]:
        with self._snapshot_lock:
            return copy.deepcopy(self._snapshot)

    def start(self) -> None:
        if self.is_running:
            return

        bridge = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "DofusWindowManagerBridge/1"

            def log_message(self, _format: str, *_args: object) -> None:
                return

            def _send_json(self, status: int, payload: dict[str, object]) -> None:
                body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def _read_json(self) -> dict[str, object]:
                content_type = (self.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
                if content_type != "application/json":
                    raise ValueError("Content-Type application/json requis.")

                try:
                    length = int(self.headers.get("Content-Length") or "0")
                except ValueError as exc:
                    raise ValueError("Content-Length invalide.") from exc
                if length <= 0:
                    return {}
                if length > bridge._max_body_bytes:
                    raise ValueError("Corps de requête trop volumineux.")

                try:
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ValueError("JSON invalide.") from exc
                if not isinstance(payload, dict):
                    raise ValueError("Le corps JSON doit être un objet.")
                return payload

            def do_GET(self) -> None:
                bridge._record_request()
                if self.path == "/v1/status":
                    self._send_json(200, bridge.get_snapshot())
                    return
                self._send_json(404, {"ok": False, "error": "Route inconnue."})

            def do_POST(self) -> None:
                bridge._record_request()
                routes = {
                    "/v1/focus": "focus",
                    "/v1/rotate": "rotate",
                    "/v1/refresh": "refresh",
                    "/v1/show": "show",
                    "/v1/toggle-ignore": "toggle_ignore",
                    "/v1/reorder": "reorder",
                }
                command = routes.get(self.path)
                if command is None:
                    self._send_json(404, {"ok": False, "error": "Route inconnue."})
                    return

                # Node.js does not send Origin for these calls. Rejecting it keeps
                # browser pages from driving the local bridge.
                if self.headers.get("Origin"):
                    self._send_json(403, {"ok": False, "error": "Origine navigateur refusée."})
                    return

                try:
                    payload = self._read_json()
                except ValueError as exc:
                    self._send_json(400, {"ok": False, "error": str(exc)})
                    return

                try:
                    result = dict(bridge._dispatch(command, payload))
                except TimeoutError:
                    self._send_json(504, {"ok": False, "error": "L'application ne répond pas."})
                    return
                except Exception:
                    self._send_json(503, {"ok": False, "error": "Commande indisponible."})
                    return

                default_status = 200 if result.get("ok", False) else 409
                status = int(result.pop("_status", default_status))
                self._send_json(status, result)

        server = _LocalThreadingHTTPServer((self._host, self._requested_port), Handler)
        thread = threading.Thread(target=server.serve_forever, name="DWMStreamDeckBridge", daemon=True)
        self._server = server
        self._thread = thread
        thread.start()

    def stop(self) -> None:
        server = self._server
        thread = self._thread
        if server is None:
            return

        server.shutdown()
        server.server_close()
        if thread and thread is not threading.current_thread():
            thread.join(timeout=2.0)
        self._server = None
        self._thread = None
