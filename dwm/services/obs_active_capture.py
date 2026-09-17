from __future__ import annotations

import queue
import threading
from dataclasses import dataclass


try:
    import obsws_python as _obs
except Exception:  # pragma: no cover - optional runtime guard
    _obs = None


DEFAULT_OBS_HOST = "127.0.0.1"
DEFAULT_OBS_PORT = 4455
DEFAULT_GAME_CAPTURE_SOURCE = "[Dofus] Client actif"
GAME_CAPTURE_HOTKEY_NAME = "hotkey_start"


@dataclass(frozen=True)
class OBSActiveCaptureConfig:
    enabled: bool = False
    host: str = DEFAULT_OBS_HOST
    port: int = DEFAULT_OBS_PORT
    password: str = ""
    source_name: str = DEFAULT_GAME_CAPTURE_SOURCE

    def normalized(self) -> "OBSActiveCaptureConfig":
        host = (self.host or DEFAULT_OBS_HOST).strip()
        if host not in {"127.0.0.1", "localhost", "::1"}:
            host = DEFAULT_OBS_HOST
        try:
            port = int(self.port)
        except (TypeError, ValueError, OverflowError):
            port = DEFAULT_OBS_PORT
        port = max(1, min(65535, port))
        source_name = (self.source_name or DEFAULT_GAME_CAPTURE_SOURCE).strip()
        if not source_name:
            source_name = DEFAULT_GAME_CAPTURE_SOURCE
        return OBSActiveCaptureConfig(
            enabled=bool(self.enabled),
            host=host,
            port=port,
            password=str(self.password or ""),
            source_name=source_name[:256],
        )


def probe_obs_connection(config: OBSActiveCaptureConfig) -> tuple[bool, str]:
    """Test OBS WebSocket without mutating scenes or sources."""
    normalized = config.normalized()
    if _obs is None:
        return False, "Le module obsws-python est indisponible."
    try:
        client = _obs.ReqClient(
            host=normalized.host,
            port=normalized.port,
            password=normalized.password,
            timeout=2,
        )
        response = client.send("GetVersion", raw=True)
        version = ""
        if isinstance(response, dict):
            version = str(response.get("obsVersion") or response.get("obs_version") or "")
        return True, f"OBS WebSocket connecté{f' · OBS {version}' if version else ''}."
    except Exception as exc:
        return False, f"Connexion OBS impossible : {exc}"


class OBSActiveCaptureBridge:
    """Trigger one OBS Game Capture source whenever Dofus takes focus.

    OBS performs the actual foreground-window lookup. DWM never sends a HWND to
    OBS; it only triggers the source-specific Game Capture hotkey.
    """

    def __init__(self, config: OBSActiveCaptureConfig):
        self._lock = threading.Lock()
        self._config = config.normalized()
        self._commands: queue.Queue[str] = queue.Queue(maxsize=1)
        self._stop = threading.Event()
        self._client = None
        self.last_error = ""
        self._thread = threading.Thread(
            target=self._run,
            name="DWMOBSActiveCapture",
            daemon=True,
        )
        self._thread.start()

    def configure(self, config: OBSActiveCaptureConfig) -> None:
        normalized = config.normalized()
        with self._lock:
            if normalized == self._config:
                return
            self._config = normalized
            self._client = None
            self.last_error = ""

    def trigger_capture(self) -> bool:
        with self._lock:
            enabled = self._config.enabled
        if not enabled or self._stop.is_set():
            return False

        # Only the latest focus matters. If the worker is briefly busy, discard
        # an obsolete trigger rather than replaying stale focus transitions.
        try:
            while True:
                self._commands.get_nowait()
                self._commands.task_done()
        except queue.Empty:
            pass
        try:
            self._commands.put_nowait("capture")
            return True
        except queue.Full:
            return False

    def stop(self) -> None:
        self._stop.set()
        try:
            self._commands.put_nowait("stop")
        except queue.Full:
            pass
        if self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def _snapshot(self) -> OBSActiveCaptureConfig:
        with self._lock:
            return self._config

    def _ensure_client(self, config: OBSActiveCaptureConfig):
        if _obs is None:
            raise RuntimeError("obsws-python est indisponible")
        if self._client is None:
            self._client = _obs.ReqClient(
                host=config.host,
                port=config.port,
                password=config.password,
                timeout=2,
            )
        return self._client

    def _trigger_once(self) -> None:
        config = self._snapshot()
        if not config.enabled:
            return
        try:
            client = self._ensure_client(config)
            client.send(
                "TriggerHotkeyByName",
                {
                    "hotkeyName": GAME_CAPTURE_HOTKEY_NAME,
                    "contextName": config.source_name,
                },
            )
            self.last_error = ""
        except Exception as exc:
            self.last_error = str(exc)
            self._client = None

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                command = self._commands.get(timeout=0.25)
            except queue.Empty:
                continue
            try:
                if command == "stop":
                    return
                if command == "capture":
                    self._trigger_once()
            finally:
                self._commands.task_done()
