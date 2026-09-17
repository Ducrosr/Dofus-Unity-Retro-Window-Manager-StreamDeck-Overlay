from __future__ import annotations

import re
import threading
from dataclasses import dataclass


from .window_telemetry import WindowTelemetry


try:
    import obsws_python as _obs
except Exception:  # pragma: no cover - optional runtime guard
    _obs = None


DEFAULT_OBS_HOST = "127.0.0.1"
DEFAULT_OBS_PORT = 4455
DEFAULT_CAPTURE_SCENE = "[DWM] Dofus Active"
DEFAULT_SOURCE_PREFIX = "[DWM] Dofus Capture"
WINDOW_CAPTURE_KIND = "window_capture"
WINDOW_CAPTURE_METHOD_WGC = 2
WINDOW_PRIORITY_TITLE = 1


@dataclass(frozen=True)
class OBSActiveCaptureConfig:
    enabled: bool = False
    host: str = DEFAULT_OBS_HOST
    port: int = DEFAULT_OBS_PORT
    password: str = ""
    scene_name: str = DEFAULT_CAPTURE_SCENE
    source_prefix: str = DEFAULT_SOURCE_PREFIX
    capture_cursor: bool = False
    force_sdr: bool = False

    def normalized(self) -> "OBSActiveCaptureConfig":
        host = (self.host or DEFAULT_OBS_HOST).strip()
        if host not in {"127.0.0.1", "localhost", "::1"}:
            host = DEFAULT_OBS_HOST
        try:
            port = int(self.port)
        except (TypeError, ValueError, OverflowError):
            port = DEFAULT_OBS_PORT
        port = max(1, min(65535, port))
        scene_name = (self.scene_name or DEFAULT_CAPTURE_SCENE).strip()
        source_prefix = (self.source_prefix or DEFAULT_SOURCE_PREFIX).strip()
        return OBSActiveCaptureConfig(
            enabled=bool(self.enabled),
            host=host,
            port=port,
            password=str(self.password or ""),
            scene_name=(scene_name or DEFAULT_CAPTURE_SCENE)[:256],
            source_prefix=(source_prefix or DEFAULT_SOURCE_PREFIX)[:220],
            capture_cursor=bool(self.capture_cursor),
            force_sdr=bool(self.force_sdr),
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


def _input_settings(window: WindowTelemetry, config: OBSActiveCaptureConfig) -> dict[str, object]:
    return {
        "window": window.obs_window_selector,
        "method": WINDOW_CAPTURE_METHOD_WGC,
        "priority": WINDOW_PRIORITY_TITLE,
        "cursor": bool(config.capture_cursor),
        "force_sdr": bool(config.force_sdr),
        "compatibility": False,
        "client_area": True,
        "capture_audio": False,
    }


def _slot_name(prefix: str, slot: int) -> str:
    return f"{prefix} {slot:02d}"


class OBSActiveCaptureBridge:
    """Maintain a dynamic OBS Window Capture pool for Dofus clients.

    The pool has no fixed client count. Sources are created lazily as concurrent
    clients appear, retained for reuse, and only visibility changes on ordinary
    focus swaps. A source target is updated only when a client appears, restarts
    or changes identity/title.
    """

    def __init__(self, config: OBSActiveCaptureConfig):
        self._lock = threading.Lock()
        self._config = config.normalized()
        self._windows: dict[int, WindowTelemetry] = {}
        self._active_hwnd: int | None = None

        self._stop = threading.Event()
        self._wake = threading.Event()
        self._client = None
        self.last_error = ""

        self._slot_by_session: dict[str, int] = {}
        self._session_by_slot: dict[int, str] = {}
        self._item_id_by_slot: dict[int, int] = {}
        self._selector_by_slot: dict[int, str] = {}
        self._known_slots: set[int] = set()
        self._visible_slot: int | None = None
        self._obs_layout_ready = False

        self._thread = threading.Thread(
            target=self._run,
            name="DWMOBSWindowPool",
            daemon=True,
        )
        self._thread.start()

    def configure(self, config: OBSActiveCaptureConfig) -> None:
        normalized = config.normalized()
        with self._lock:
            if normalized == self._config:
                return
            connection_changed = (
                normalized.host,
                normalized.port,
                normalized.password,
            ) != (
                self._config.host,
                self._config.port,
                self._config.password,
            )
            layout_changed = (
                normalized.scene_name,
                normalized.source_prefix,
            ) != (
                self._config.scene_name,
                self._config.source_prefix,
            )
            capture_settings_changed = (
                normalized.capture_cursor,
                normalized.force_sdr,
            ) != (
                self._config.capture_cursor,
                self._config.force_sdr,
            )
            self._config = normalized
            if connection_changed:
                self._client = None
            if connection_changed or layout_changed:
                self._reset_obs_state_locked()
            elif capture_settings_changed:
                self._selector_by_slot.clear()
        self._wake.set()

    def sync_windows(
        self,
        windows: list[WindowTelemetry] | tuple[WindowTelemetry, ...],
        active_hwnd: int | None,
    ) -> None:
        with self._lock:
            self._windows = {int(window.hwnd): window for window in windows}
            self._active_hwnd = int(active_hwnd) if active_hwnd else None
        self._wake.set()

    def set_active_window(self, hwnd: int | None) -> None:
        with self._lock:
            self._active_hwnd = int(hwnd) if hwnd else None
        self._wake.set()

    def stop(self) -> None:
        self._stop.set()
        self._wake.set()
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def _reset_obs_state_locked(self) -> None:
        self._slot_by_session.clear()
        self._session_by_slot.clear()
        self._item_id_by_slot.clear()
        self._selector_by_slot.clear()
        self._known_slots.clear()
        self._visible_slot = None
        self._obs_layout_ready = False

    def _snapshot(self) -> tuple[OBSActiveCaptureConfig, dict[int, WindowTelemetry], int | None]:
        with self._lock:
            return self._config, dict(self._windows), self._active_hwnd

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

    @staticmethod
    def _send(client, request: str, data: dict[str, object] | None = None) -> dict[str, object]:
        if data is None:
            response = client.send(request, raw=True)
        else:
            response = client.send(request, data, raw=True)
        return response if isinstance(response, dict) else {}

    def _ensure_scene(self, client, config: OBSActiveCaptureConfig) -> None:
        response = self._send(client, "GetSceneList")
        scenes = response.get("scenes") if isinstance(response, dict) else None
        names = {
            str(scene.get("sceneName") or "")
            for scene in (scenes or [])
            if isinstance(scene, dict)
        }
        if config.scene_name not in names:
            self._send(
                client,
                "CreateScene",
                {"sceneName": config.scene_name},
            )

    def _discover_existing_slots(self, client, config: OBSActiveCaptureConfig) -> None:
        escaped_prefix = re.escape(config.source_prefix)
        pattern = re.compile(rf"^{escaped_prefix}\s+(\d+)$")
        response = self._send(
            client,
            "GetInputList",
            {"inputKind": WINDOW_CAPTURE_KIND},
        )
        for entry in response.get("inputs", []) or []:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("inputName") or "")
            match = pattern.match(name)
            if not match:
                continue
            slot = int(match.group(1))
            if slot <= 0:
                continue
            self._known_slots.add(slot)
            try:
                item = self._send(
                    client,
                    "GetSceneItemId",
                    {
                        "sceneName": config.scene_name,
                        "sourceName": name,
                    },
                )
                item_id = int(item.get("sceneItemId") or 0)
            except Exception:
                item = self._send(
                    client,
                    "CreateSceneItem",
                    {
                        "sceneName": config.scene_name,
                        "sourceName": name,
                        "sceneItemEnabled": False,
                    },
                )
                item_id = int(item.get("sceneItemId") or 0)
            if item_id:
                self._item_id_by_slot[slot] = item_id

    def _prepare_obs_layout(self, client, config: OBSActiveCaptureConfig) -> None:
        if self._obs_layout_ready:
            return
        self._ensure_scene(client, config)
        self._discover_existing_slots(client, config)
        self._visible_slot = None
        for slot, item_id in sorted(self._item_id_by_slot.items()):
            self._send(
                client,
                "SetSceneItemEnabled",
                {
                    "sceneName": config.scene_name,
                    "sceneItemId": item_id,
                    "sceneItemEnabled": False,
                },
            )
        self._obs_layout_ready = True

    def _reconcile_assignments(self, windows: dict[int, WindowTelemetry]) -> None:
        current_sessions = {window.session_id for window in windows.values()}

        for session_id, slot in list(self._slot_by_session.items()):
            if session_id in current_sessions:
                continue
            self._slot_by_session.pop(session_id, None)
            self._session_by_slot.pop(slot, None)

        used_slots = set(self._session_by_slot)
        for window in sorted(
            windows.values(),
            key=lambda item: (item.process_created_100ns, item.pid, item.hwnd),
        ):
            if window.session_id in self._slot_by_session:
                continue
            slot = 1
            while slot in used_slots:
                slot += 1
            self._slot_by_session[window.session_id] = slot
            self._session_by_slot[slot] = window.session_id
            used_slots.add(slot)

    def _ensure_slot(
        self,
        client,
        config: OBSActiveCaptureConfig,
        slot: int,
        window: WindowTelemetry,
    ) -> None:
        source_name = _slot_name(config.source_prefix, slot)
        settings = _input_settings(window, config)

        if slot not in self._known_slots:
            created = self._send(
                client,
                "CreateInput",
                {
                    "sceneName": config.scene_name,
                    "inputName": source_name,
                    "inputKind": WINDOW_CAPTURE_KIND,
                    "inputSettings": settings,
                    "sceneItemEnabled": False,
                },
            )
            item_id = int(created.get("sceneItemId") or 0)
            if not item_id:
                raise RuntimeError(f"OBS n'a pas renvoyé d'identifiant pour {source_name}.")
            self._known_slots.add(slot)
            self._item_id_by_slot[slot] = item_id
            self._selector_by_slot[slot] = window.obs_window_selector
            return

        if slot not in self._item_id_by_slot:
            try:
                existing = self._send(
                    client,
                    "GetSceneItemId",
                    {
                        "sceneName": config.scene_name,
                        "sourceName": source_name,
                    },
                )
                item_id = int(existing.get("sceneItemId") or 0)
            except Exception:
                created_item = self._send(
                    client,
                    "CreateSceneItem",
                    {
                        "sceneName": config.scene_name,
                        "sourceName": source_name,
                        "sceneItemEnabled": False,
                    },
                )
                item_id = int(created_item.get("sceneItemId") or 0)
            if not item_id:
                raise RuntimeError(f"Impossible d'ajouter {source_name} à la scène OBS.")
            self._item_id_by_slot[slot] = item_id

        selector = window.obs_window_selector
        if self._selector_by_slot.get(slot) != selector:
            self._send(
                client,
                "SetInputSettings",
                {
                    "inputName": source_name,
                    "inputSettings": settings,
                    "overlay": True,
                },
            )
            self._selector_by_slot[slot] = selector

    def _desired_visible_slot(
        self,
        windows: dict[int, WindowTelemetry],
        active_hwnd: int | None,
    ) -> int | None:
        if not active_hwnd:
            if self._visible_slot in self._session_by_slot:
                return self._visible_slot
            return None
        active = windows.get(active_hwnd)
        if active is None:
            if self._visible_slot in self._session_by_slot:
                return self._visible_slot
            return None
        return self._slot_by_session.get(active.session_id)

    def _set_visibility(
        self,
        client,
        config: OBSActiveCaptureConfig,
        target_slot: int | None,
    ) -> None:
        if target_slot == self._visible_slot:
            return

        # Enable the new capture first so there is never an intentional empty
        # frame between two already-initialized Window Capture sources.
        if target_slot is not None:
            target_item = self._item_id_by_slot.get(target_slot)
            if target_item:
                self._send(
                    client,
                    "SetSceneItemEnabled",
                    {
                        "sceneName": config.scene_name,
                        "sceneItemId": target_item,
                        "sceneItemEnabled": True,
                    },
                )

        previous_slot = self._visible_slot
        if previous_slot is not None and previous_slot != target_slot:
            previous_item = self._item_id_by_slot.get(previous_slot)
            if previous_item:
                self._send(
                    client,
                    "SetSceneItemEnabled",
                    {
                        "sceneName": config.scene_name,
                        "sceneItemId": previous_item,
                        "sceneItemEnabled": False,
                    },
                )

        self._visible_slot = target_slot

    def _disable_unassigned_slots(
        self,
        client,
        config: OBSActiveCaptureConfig,
    ) -> None:
        assigned = set(self._session_by_slot)
        for slot in sorted(self._known_slots - assigned):
            if slot == self._visible_slot:
                continue
            item_id = self._item_id_by_slot.get(slot)
            if item_id:
                self._send(
                    client,
                    "SetSceneItemEnabled",
                    {
                        "sceneName": config.scene_name,
                        "sceneItemId": item_id,
                        "sceneItemEnabled": False,
                    },
                )

    def _reconcile_once(self) -> None:
        config, windows, active_hwnd = self._snapshot()
        if not config.enabled:
            return

        try:
            client = self._ensure_client(config)
            self._prepare_obs_layout(client, config)
            self._reconcile_assignments(windows)

            by_session = {window.session_id: window for window in windows.values()}
            for slot, session_id in sorted(self._session_by_slot.items()):
                window = by_session.get(session_id)
                if window is not None:
                    self._ensure_slot(client, config, slot, window)

            target_slot = self._desired_visible_slot(windows, active_hwnd)
            self._set_visibility(client, config, target_slot)
            self._disable_unassigned_slots(client, config)
            self.last_error = ""
        except Exception as exc:
            self.last_error = str(exc)
            self._client = None
            self._obs_layout_ready = False
            self._item_id_by_slot.clear()
            self._selector_by_slot.clear()
            self._known_slots.clear()
            self._visible_slot = None

    def _run(self) -> None:
        while not self._stop.is_set():
            self._wake.wait(timeout=0.5)
            self._wake.clear()
            if self._stop.is_set():
                return
            self._reconcile_once()
