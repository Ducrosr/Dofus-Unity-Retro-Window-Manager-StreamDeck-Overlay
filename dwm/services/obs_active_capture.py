from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass

from ..models import GameWindow
from .obs_overlay_capture import (
    OVERLAY_WINDOW_TITLE,
    POPUP_WINDOW_TITLE,
)
from .win32_enum import enum_top_level_windows
from .window_telemetry import RectSnapshot, WindowTelemetry, collect_window_telemetry


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
VISIBILITY_FILTER_NAME = "[DWM] Visibility"
VISIBILITY_FILTER_KIND = "color_filter_v2"
OVERLAY_SOURCE_NAME = "[DWM] Overlay"
POPUP_SOURCE_NAME = "[DWM] Focus Popup"
POPUP_COLOR_KEY_FILTER_NAME = "[DWM] Popup Color Key"
POPUP_OPACITY_FILTER_NAME = "[DWM] Popup Opacity"
POPUP_COLOR_KEY_FILTER_KIND = "color_key_filter_v2"
POPUP_OPACITY_FILTER_KIND = "color_filter_v2"
ADVSS_VENDOR_NAME = "AdvancedSceneSwitcher"
ADVSS_SET_VARIABLES_REQUEST = "AdvancedSceneSwitcherSetVariables"
ADVSS_GAME_VARIABLE_NAME = "Game"
ADVSS_RETRY_SECONDS = 30.0
OBS_CAPTURE_HANDOFF_DELAY_SECONDS = 0.033


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
    popup_opacity: float = 0.88

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
            popup_opacity=max(0.0, min(1.0, float(self.popup_opacity))),
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


def _input_settings(
    window: WindowTelemetry,
    config: OBSActiveCaptureConfig,
    *,
    capture_cursor: bool | None = None,
) -> dict[str, object]:
    return {
        "window": window.obs_window_selector,
        "method": WINDOW_CAPTURE_METHOD_WGC,
        "priority": WINDOW_PRIORITY_TITLE,
        "cursor": bool(config.capture_cursor if capture_cursor is None else capture_cursor),
        "force_sdr": bool(config.force_sdr),
        "compatibility": False,
        "client_area": True,
        "capture_audio": False,
    }


def _slot_name(prefix: str, slot: int) -> str:
    return f"{prefix} {slot:02d}"


def advanced_scene_switcher_game_value(game_mode: str | None) -> str:
    return "Dofus Retro" if str(game_mode or "").strip().lower() == "retro" else "Dofus Unity"


@dataclass(frozen=True)
class OBSSceneTransform:
    position_x: float
    position_y: float
    scale_x: float
    scale_y: float

    def rounded_signature(self) -> tuple[float, float, float, float]:
        return (
            round(self.position_x, 3),
            round(self.position_y, 3),
            round(self.scale_x, 6),
            round(self.scale_y, 6),
        )


def _capture_rect(window: WindowTelemetry) -> RectSnapshot:
    client = window.client_rect_screen
    if client.width > 0 and client.height > 0:
        return client
    return window.window_rect


def fit_window_to_canvas(
    window: WindowTelemetry,
    base_width: int,
    base_height: int,
) -> OBSSceneTransform | None:
    rect = _capture_rect(window)
    if rect.width <= 0 or rect.height <= 0 or base_width <= 0 or base_height <= 0:
        return None
    scale = min(base_width / rect.width, base_height / rect.height)
    rendered_width = rect.width * scale
    rendered_height = rect.height * scale
    return OBSSceneTransform(
        position_x=(base_width - rendered_width) / 2.0,
        position_y=(base_height - rendered_height) / 2.0,
        scale_x=scale,
        scale_y=scale,
    )


def project_window_over_reference(
    window: WindowTelemetry,
    reference: WindowTelemetry,
    base_width: int,
    base_height: int,
) -> OBSSceneTransform | None:
    reference_transform = fit_window_to_canvas(reference, base_width, base_height)
    if reference_transform is None:
        return None
    reference_rect = _capture_rect(reference)
    window_rect = _capture_rect(window)
    if window_rect.width <= 0 or window_rect.height <= 0:
        return None

    # Window/client rectangles and WGC source pixels are both expressed in
    # desktop physical pixels. Apply the same uniform scale as the active Dofus
    # client so the DWM interface retains its real desktop position relative to
    # the game after the game is fitted into the OBS base canvas.
    return OBSSceneTransform(
        position_x=(
            reference_transform.position_x
            + (window_rect.left - reference_rect.left) * reference_transform.scale_x
        ),
        position_y=(
            reference_transform.position_y
            + (window_rect.top - reference_rect.top) * reference_transform.scale_y
        ),
        scale_x=reference_transform.scale_x,
        scale_y=reference_transform.scale_y,
    )


class OBSActiveCaptureBridge:
    """Maintain a dynamic OBS Window Capture pool for Dofus clients.

    The pool has no fixed client count. Sources are created lazily as concurrent
    clients appear and retained for reuse. Only the focused Dofus scene item is
    enabled in normal operation; focus swaps enable the new item first and then
    disable the previous one immediately. A source target is updated only when a
    client appears, restarts or changes identity/title.
    """

    def __init__(self, config: OBSActiveCaptureConfig):
        self._lock = threading.Lock()
        self._config = config.normalized()
        self._windows: dict[int, WindowTelemetry] = {}
        self._active_hwnd: int | None = None
        self._game_mode = "unity"
        self._advss_game_value_sent: str | None = None
        self._advss_retry_after = 0.0

        self._stop = threading.Event()
        self._wake = threading.Event()
        self._client = None
        self.last_error = ""

        self._slot_by_session: dict[str, int] = {}
        self._session_by_slot: dict[int, str] = {}
        self._item_id_by_slot: dict[int, int] = {}
        self._selector_by_slot: dict[int, str] = {}
        self._known_slots: set[int] = set()
        self._filter_ready_slots: set[int] = set()
        self._opacity_by_slot: dict[int, float] = {}
        self._enabled_slots: set[int] = set()
        self._visible_slot: int | None = None
        self._interface_known_inputs: set[str] = set()
        self._interface_item_ids: dict[str, int] = {}
        self._interface_selectors: dict[str, str] = {}
        self._popup_filters_ready = False
        self._popup_filter_opacity: float | None = None
        self._interface_order_dirty = True
        self._canvas_size: tuple[int, int] | None = None
        self._transform_signatures: dict[int, tuple[float, float, float, float]] = {}
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
                normalized.popup_opacity,
            ) != (
                self._config.capture_cursor,
                self._config.force_sdr,
                self._config.popup_opacity,
            )
            self._config = normalized
            if connection_changed:
                self._client = None
                self._advss_game_value_sent = None
                self._advss_retry_after = 0.0
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

    def set_game_mode(self, game_mode: str) -> None:
        normalized = "retro" if str(game_mode or "").strip().lower() == "retro" else "unity"
        with self._lock:
            if normalized != self._game_mode:
                self._game_mode = normalized
                self._advss_game_value_sent = None
                self._advss_retry_after = 0.0
        self._wake.set()

    def request_refresh(self) -> None:
        self._wake.set()

    def stop(self) -> None:
        self._stop.set()
        self._wake.set()
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._hide_interface_sources_on_shutdown()

    def _hide_interface_sources_on_shutdown(self) -> None:
        """Best-effort cleanup of DWM-only OBS layers before Tk destroys them.

        Dofus capture slots deliberately remain untouched so the last active
        game can stay visible in OBS after DWM exits. Only the DWM overlay and
        focus popup are disabled.
        """
        with self._lock:
            config = self._config
            client = self._client
            item_ids = dict(self._interface_item_ids)

        if client is None:
            return

        for source_name in (OVERLAY_SOURCE_NAME, POPUP_SOURCE_NAME):
            item_id = item_ids.get(source_name)
            if not item_id:
                try:
                    response = self._send(
                        client,
                        "GetSceneItemId",
                        {
                            "sceneName": config.scene_name,
                            "sourceName": source_name,
                        },
                    )
                    item_id = int(response.get("sceneItemId") or 0)
                except Exception:
                    item_id = 0
            if not item_id:
                continue
            try:
                self._send(
                    client,
                    "SetSceneItemEnabled",
                    {
                        "sceneName": config.scene_name,
                        "sceneItemId": item_id,
                        "sceneItemEnabled": False,
                    },
                )
            except Exception:
                # OBS may already be closed. Shutdown must stay reliable.
                continue

    def _reset_obs_state_locked(self) -> None:
        self._slot_by_session.clear()
        self._session_by_slot.clear()
        self._item_id_by_slot.clear()
        self._selector_by_slot.clear()
        self._known_slots.clear()
        self._filter_ready_slots.clear()
        self._opacity_by_slot.clear()
        self._enabled_slots.clear()
        self._visible_slot = None
        self._interface_known_inputs.clear()
        self._interface_item_ids.clear()
        self._interface_selectors.clear()
        self._popup_filters_ready = False
        self._popup_filter_opacity = None
        self._interface_order_dirty = True
        self._canvas_size = None
        self._transform_signatures.clear()
        self._obs_layout_ready = False

    def _snapshot(
        self,
    ) -> tuple[OBSActiveCaptureConfig, dict[int, WindowTelemetry], int | None, str]:
        with self._lock:
            return (
                self._config,
                dict(self._windows),
                self._active_hwnd,
                self._game_mode,
            )

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
            self._advss_game_value_sent = None
            self._advss_retry_after = 0.0
        return self._client

    @staticmethod
    def _send(client, request: str, data: dict[str, object] | None = None) -> dict[str, object]:
        if data is None:
            response = client.send(request, raw=True)
        else:
            response = client.send(request, data, raw=True)
        return response if isinstance(response, dict) else {}

    def _sync_advanced_scene_switcher_game(
        self,
        client,
        game_mode: str,
    ) -> None:
        desired = advanced_scene_switcher_game_value(game_mode)
        if self._advss_game_value_sent == desired:
            return
        now = time.monotonic()
        if now < self._advss_retry_after:
            return
        try:
            self._send(
                client,
                "CallVendorRequest",
                {
                    "vendorName": ADVSS_VENDOR_NAME,
                    "requestType": ADVSS_SET_VARIABLES_REQUEST,
                    "requestData": {
                        "variables": [
                            {
                                "name": ADVSS_GAME_VARIABLE_NAME,
                                "value": desired,
                            }
                        ]
                    },
                },
            )
            self._advss_game_value_sent = desired
            self._advss_retry_after = 0.0
        except Exception:
            # Advanced Scene Switcher is optional. Its absence must never break
            # DWM's native OBS capture integration.
            self._advss_retry_after = now + ADVSS_RETRY_SECONDS

    def _get_canvas_size(self, client) -> tuple[int, int] | None:
        if self._canvas_size is not None:
            return self._canvas_size
        response = self._send(client, "GetVideoSettings")
        try:
            base_width = int(response.get("baseWidth") or 0)
            base_height = int(response.get("baseHeight") or 0)
        except (TypeError, ValueError):
            return None
        if base_width <= 0 or base_height <= 0:
            return None
        self._canvas_size = (base_width, base_height)
        return self._canvas_size

    def _set_scene_item_transform(
        self,
        client,
        config: OBSActiveCaptureConfig,
        item_id: int | None,
        transform: OBSSceneTransform | None,
    ) -> None:
        if not item_id or transform is None:
            return
        signature = transform.rounded_signature()
        if self._transform_signatures.get(item_id) == signature:
            return
        self._send(
            client,
            "SetSceneItemTransform",
            {
                "sceneName": config.scene_name,
                "sceneItemId": item_id,
                "sceneItemTransform": {
                    "positionX": float(transform.position_x),
                    "positionY": float(transform.position_y),
                    "scaleX": float(transform.scale_x),
                    "scaleY": float(transform.scale_y),
                    "rotation": 0.0,
                    "alignment": 5,
                },
            },
        )
        self._transform_signatures[item_id] = signature

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
        response = self._send(client, "GetInputList")
        self._interface_known_inputs = {
            str(entry.get("inputName") or "")
            for entry in response.get("inputs", []) or []
            if isinstance(entry, dict)
        }
        self._visible_slot = None
        for _slot, item_id in sorted(self._item_id_by_slot.items()):
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

    @staticmethod
    def _find_interface_window(title: str) -> WindowTelemetry | None:
        for hwnd, window_title in enum_top_level_windows(
            class_name=None,
            visible_only=True,
        ):
            if window_title != title:
                continue
            try:
                return collect_window_telemetry(
                    GameWindow(
                        hwnd=int(hwnd),
                        title=window_title,
                        pseudo="",
                        character_class="",
                    ),
                    "dwm",
                )
            except Exception:
                return None
        return None

    def _ensure_interface_capture(
        self,
        client,
        config: OBSActiveCaptureConfig,
        *,
        source_name: str,
        window: WindowTelemetry | None,
    ) -> int | None:
        item_id = self._interface_item_ids.get(source_name)
        if window is None:
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
            return item_id

        settings = _input_settings(window, config, capture_cursor=False)
        if source_name not in self._interface_known_inputs:
            created = self._send(
                client,
                "CreateInput",
                {
                    "sceneName": config.scene_name,
                    "inputName": source_name,
                    "inputKind": WINDOW_CAPTURE_KIND,
                    "inputSettings": settings,
                    "sceneItemEnabled": True,
                },
            )
            item_id = int(created.get("sceneItemId") or 0)
            if not item_id:
                raise RuntimeError(
                    f"OBS n'a pas renvoyé d'identifiant pour {source_name}."
                )
            self._interface_known_inputs.add(source_name)
            self._interface_item_ids[source_name] = item_id
            self._interface_selectors[source_name] = window.obs_window_selector
            self._interface_order_dirty = True
        else:
            if not item_id:
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
                            "sceneItemEnabled": True,
                        },
                    )
                    item_id = int(created_item.get("sceneItemId") or 0)
                if not item_id:
                    raise RuntimeError(
                        f"Impossible d'ajouter {source_name} à la scène OBS."
                    )
                self._interface_item_ids[source_name] = item_id
                self._interface_order_dirty = True

            if self._interface_selectors.get(source_name) != window.obs_window_selector:
                self._send(
                    client,
                    "SetInputSettings",
                    {
                        "inputName": source_name,
                        "inputSettings": settings,
                        "overlay": True,
                    },
                )
                self._interface_selectors[source_name] = window.obs_window_selector

            self._send(
                client,
                "SetSceneItemEnabled",
                {
                    "sceneName": config.scene_name,
                    "sceneItemId": item_id,
                    "sceneItemEnabled": True,
                },
            )

        return item_id

    def _ensure_popup_filters(
        self,
        client,
        config: OBSActiveCaptureConfig,
    ) -> None:
        if (
            self._popup_filters_ready
            and self._popup_filter_opacity == float(config.popup_opacity)
        ):
            return

        response = self._send(
            client,
            "GetSourceFilterList",
            {"sourceName": POPUP_SOURCE_NAME},
        )
        filters = {
            str(item.get("filterName") or ""): item
            for item in response.get("filters", []) or []
            if isinstance(item, dict)
        }

        color_key_settings = {
            "key_color_type": "magenta",
            "key_color": 0xFF00FF,
            "similarity": 80,
            "smoothness": 50,
            "opacity": 1.0,
        }
        if POPUP_COLOR_KEY_FILTER_NAME not in filters:
            self._send(
                client,
                "CreateSourceFilter",
                {
                    "sourceName": POPUP_SOURCE_NAME,
                    "filterName": POPUP_COLOR_KEY_FILTER_NAME,
                    "filterKind": POPUP_COLOR_KEY_FILTER_KIND,
                    "filterSettings": color_key_settings,
                },
            )
        else:
            self._send(
                client,
                "SetSourceFilterEnabled",
                {
                    "sourceName": POPUP_SOURCE_NAME,
                    "filterName": POPUP_COLOR_KEY_FILTER_NAME,
                    "filterEnabled": True,
                },
            )
            self._send(
                client,
                "SetSourceFilterSettings",
                {
                    "sourceName": POPUP_SOURCE_NAME,
                    "filterName": POPUP_COLOR_KEY_FILTER_NAME,
                    "filterSettings": color_key_settings,
                    "overlay": True,
                },
            )

        opacity_settings = {"opacity": float(config.popup_opacity)}
        if POPUP_OPACITY_FILTER_NAME not in filters:
            self._send(
                client,
                "CreateSourceFilter",
                {
                    "sourceName": POPUP_SOURCE_NAME,
                    "filterName": POPUP_OPACITY_FILTER_NAME,
                    "filterKind": POPUP_OPACITY_FILTER_KIND,
                    "filterSettings": opacity_settings,
                },
            )
        else:
            self._send(
                client,
                "SetSourceFilterEnabled",
                {
                    "sourceName": POPUP_SOURCE_NAME,
                    "filterName": POPUP_OPACITY_FILTER_NAME,
                    "filterEnabled": True,
                },
            )
            self._send(
                client,
                "SetSourceFilterSettings",
                {
                    "sourceName": POPUP_SOURCE_NAME,
                    "filterName": POPUP_OPACITY_FILTER_NAME,
                    "filterSettings": opacity_settings,
                    "overlay": True,
                },
            )

        # Preserve the manually validated processing order: key removal first,
        # opacity correction second.
        self._send(
            client,
            "SetSourceFilterIndex",
            {
                "sourceName": POPUP_SOURCE_NAME,
                "filterName": POPUP_COLOR_KEY_FILTER_NAME,
                "filterIndex": 0,
            },
        )
        self._send(
            client,
            "SetSourceFilterIndex",
            {
                "sourceName": POPUP_SOURCE_NAME,
                "filterName": POPUP_OPACITY_FILTER_NAME,
                "filterIndex": 1,
            },
        )
        self._popup_filters_ready = True
        self._popup_filter_opacity = float(config.popup_opacity)

    def _ensure_interface_order(
        self,
        client,
        config: OBSActiveCaptureConfig,
        *,
        overlay_item_id: int | None,
        popup_item_id: int | None,
    ) -> None:
        if not self._interface_order_dirty:
            return
        if not overlay_item_id and not popup_item_id:
            return
        response = self._send(
            client,
            "GetSceneItemList",
            {"sceneName": config.scene_name},
        )
        scene_items = response.get("sceneItems", []) or []
        if not scene_items:
            return
        top_index = len(scene_items) - 1

        # obs-websocket defines sceneItemIndex 0 as the bottom layer. Move the
        # overlay to the top first, then the popup to the top; this leaves the
        # popup highest, overlay directly below it, and every Dofus capture
        # underneath both — including captures created later.
        if overlay_item_id:
            self._send(
                client,
                "SetSceneItemIndex",
                {
                    "sceneName": config.scene_name,
                    "sceneItemId": overlay_item_id,
                    "sceneItemIndex": top_index,
                },
            )
        if popup_item_id:
            self._send(
                client,
                "SetSceneItemIndex",
                {
                    "sceneName": config.scene_name,
                    "sceneItemId": popup_item_id,
                    "sceneItemIndex": top_index,
                },
            )
        self._interface_order_dirty = False

    def _reconcile_interface_sources(
        self,
        client,
        config: OBSActiveCaptureConfig,
        *,
        reference_window: WindowTelemetry | None,
    ) -> None:
        overlay_window = self._find_interface_window(OVERLAY_WINDOW_TITLE)
        popup_window = self._find_interface_window(POPUP_WINDOW_TITLE)

        overlay_item_id = self._ensure_interface_capture(
            client,
            config,
            source_name=OVERLAY_SOURCE_NAME,
            window=overlay_window,
        )
        popup_item_id = self._ensure_interface_capture(
            client,
            config,
            source_name=POPUP_SOURCE_NAME,
            window=popup_window,
        )

        if popup_window is not None:
            self._ensure_popup_filters(client, config)

        canvas = self._get_canvas_size(client)
        if canvas is not None and reference_window is not None:
            base_width, base_height = canvas
            self._set_scene_item_transform(
                client,
                config,
                overlay_item_id if overlay_window is not None else None,
                (
                    project_window_over_reference(
                        overlay_window,
                        reference_window,
                        base_width,
                        base_height,
                    )
                    if overlay_window is not None
                    else None
                ),
            )
            self._set_scene_item_transform(
                client,
                config,
                popup_item_id if popup_window is not None else None,
                (
                    project_window_over_reference(
                        popup_window,
                        reference_window,
                        base_width,
                        base_height,
                    )
                    if popup_window is not None
                    else None
                ),
            )

        self._ensure_interface_order(
            client,
            config,
            overlay_item_id=overlay_item_id if overlay_window is not None else None,
            popup_item_id=popup_item_id if popup_window is not None else None,
        )

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
            self._interface_order_dirty = True
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
            self._interface_order_dirty = True

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

    def _ensure_visibility_filter(
        self,
        client,
        source_name: str,
        slot: int,
        opacity: float,
    ) -> None:
        opacity = 1.0 if opacity >= 0.5 else 0.0
        if slot not in self._filter_ready_slots:
            response = self._send(
                client,
                "GetSourceFilterList",
                {"sourceName": source_name},
            )
            filters = response.get("filters", []) or []
            existing = next(
                (
                    item
                    for item in filters
                    if isinstance(item, dict)
                    and str(item.get("filterName") or "") == VISIBILITY_FILTER_NAME
                ),
                None,
            )
            if existing is None:
                self._send(
                    client,
                    "CreateSourceFilter",
                    {
                        "sourceName": source_name,
                        "filterName": VISIBILITY_FILTER_NAME,
                        "filterKind": VISIBILITY_FILTER_KIND,
                        "filterSettings": {"opacity": opacity},
                    },
                )
            else:
                self._send(
                    client,
                    "SetSourceFilterEnabled",
                    {
                        "sourceName": source_name,
                        "filterName": VISIBILITY_FILTER_NAME,
                        "filterEnabled": True,
                    },
                )
                self._send(
                    client,
                    "SetSourceFilterSettings",
                    {
                        "sourceName": source_name,
                        "filterName": VISIBILITY_FILTER_NAME,
                        "filterSettings": {"opacity": opacity},
                        "overlay": True,
                    },
                )
            self._filter_ready_slots.add(slot)
            self._opacity_by_slot[slot] = opacity
            return

        if self._opacity_by_slot.get(slot) == opacity:
            return
        self._send(
            client,
            "SetSourceFilterSettings",
            {
                "sourceName": source_name,
                "filterName": VISIBILITY_FILTER_NAME,
                "filterSettings": {"opacity": opacity},
                "overlay": True,
            },
        )
        self._opacity_by_slot[slot] = opacity

    def _set_scene_item_enabled(
        self,
        client,
        config: OBSActiveCaptureConfig,
        slot: int,
        enabled: bool,
    ) -> None:
        item_id = self._item_id_by_slot.get(slot)
        if not item_id:
            return
        if enabled and slot in self._enabled_slots:
            return
        if not enabled and slot not in self._enabled_slots:
            return
        self._send(
            client,
            "SetSceneItemEnabled",
            {
                "sceneName": config.scene_name,
                "sceneItemId": item_id,
                "sceneItemEnabled": bool(enabled),
            },
        )
        if enabled:
            self._enabled_slots.add(slot)
        else:
            self._enabled_slots.discard(slot)

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

    def _wait_capture_handoff(self) -> None:
        """Wait briefly for a newly enabled WGC source to deliver its first frame."""
        self._stop.wait(OBS_CAPTURE_HANDOFF_DELAY_SECONDS)

    def _set_visibility(
        self,
        client,
        config: OBSActiveCaptureConfig,
        target_slot: int | None,
    ) -> None:
        if target_slot == self._visible_slot:
            return

        # Performance-first switching: a hidden OBS scene item stops "showing",
        # allowing Window Capture / WGC to release work for inactive clients.
        # Enable the new target before disabling the previous one. A very short
        # stream-side handoff window lets WGC deliver its first frame while the
        # previous capture still holds a valid image; normal operation still
        # returns to one active capture immediately after that overlap.
        previous_slot = self._visible_slot

        if target_slot is not None:
            source_name = _slot_name(config.source_prefix, target_slot)
            # Neutralise the legacy DWM opacity filter before showing a slot.
            # Older builds may have left this filter at 0 for inactive clients.
            self._ensure_visibility_filter(
                client,
                source_name,
                target_slot,
                1.0,
            )
            self._set_scene_item_enabled(
                client,
                config,
                target_slot,
                True,
            )

        if previous_slot is not None and previous_slot != target_slot:
            if target_slot is not None:
                # WGC starts asynchronously after OBS marks the new scene item
                # as visible. Keep the previous valid frame alive for a tiny
                # handoff window so OBS has time to receive the first frame of
                # the new capture. This delay only affects the stream-side
                # capture bridge; Dofus focus itself has already changed.
                self._wait_capture_handoff()
            self._set_scene_item_enabled(
                client,
                config,
                previous_slot,
                False,
            )

        self._visible_slot = target_slot

    def _disable_unassigned_slots(
        self,
        client,
        config: OBSActiveCaptureConfig,
    ) -> None:
        assigned = set(self._session_by_slot)
        for slot in sorted(self._known_slots - assigned):
            self._set_scene_item_enabled(
                client,
                config,
                slot,
                False,
            )

    def _reconcile_once(self) -> None:
        config, windows, active_hwnd, game_mode = self._snapshot()
        if not config.enabled:
            return

        try:
            client = self._ensure_client(config)
            self._sync_advanced_scene_switcher_game(client, game_mode)
            self._prepare_obs_layout(client, config)
            self._reconcile_assignments(windows)

            by_session = {window.session_id: window for window in windows.values()}
            target_slot = self._desired_visible_slot(windows, active_hwnd)
            active_window = windows.get(active_hwnd) if active_hwnd else None
            canvas = self._get_canvas_size(client)
            for slot, session_id in sorted(self._session_by_slot.items()):
                window = by_session.get(session_id)
                if window is None:
                    continue
                self._ensure_slot(client, config, slot, window)
                source_name = _slot_name(config.source_prefix, slot)
                # The opacity filter is retained only for compatibility with
                # scenes created by older DWM builds. Keep it neutral (100 %)
                # and use the scene-item enabled state as the real visibility
                # and GPU-resource control.
                self._ensure_visibility_filter(
                    client,
                    source_name,
                    slot,
                    1.0,
                )
                if canvas is not None:
                    base_width, base_height = canvas
                    self._set_scene_item_transform(
                        client,
                        config,
                        self._item_id_by_slot.get(slot),
                        fit_window_to_canvas(window, base_width, base_height),
                    )

            self._set_visibility(client, config, target_slot)
            self._disable_unassigned_slots(client, config)
            self._reconcile_interface_sources(
                client,
                config,
                reference_window=active_window,
            )
            self.last_error = ""
        except Exception as exc:
            self.last_error = str(exc)
            self._client = None
            self._advss_game_value_sent = None
            self._advss_retry_after = 0.0
            self._obs_layout_ready = False
            self._item_id_by_slot.clear()
            self._selector_by_slot.clear()
            self._known_slots.clear()
            self._filter_ready_slots.clear()
            self._opacity_by_slot.clear()
            self._enabled_slots.clear()
            self._visible_slot = None
            self._interface_known_inputs.clear()
            self._interface_item_ids.clear()
            self._interface_selectors.clear()
            self._popup_filters_ready = False
            self._popup_filter_opacity = None
            self._interface_order_dirty = True
            self._canvas_size = None
            self._transform_signatures.clear()

    def _run(self) -> None:
        while not self._stop.is_set():
            self._wake.wait(timeout=0.5)
            self._wake.clear()
            if self._stop.is_set():
                return
            self._reconcile_once()
