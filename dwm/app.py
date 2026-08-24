from __future__ import annotations

import json
import os
import queue
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import BooleanVar, Canvas, Label as TkLabel, StringVar, Text, Tk, Toplevel, filedialog, messagebox, simpledialog
from tkinter.ttk import (
    Button as TtkButton,
    Checkbutton as TtkCheckbutton,
    Combobox,
    Entry as TtkEntry,
    Frame as TtkFrame,
    Label as TtkLabel,
    LabelFrame as TtkLabelFrame,
    Notebook,
    Scrollbar,
    Spinbox,
    Style,
    Treeview,
)

from PIL import Image, ImageTk

from . import __release_tag__, __version__
from .models import GameWindow
from .services.windows import (
    extract_character_class,
    extract_pseudo_retro,
    extract_pseudo_unity,
    list_game_windows,
    list_visible_dofus_candidates,
    suspect_privilege_mismatch,
)
from .services.focus import FocusError, focus_hwnd, get_foreground_hwnd, is_window
from .services.game_mode import game_mode_label, normalize_game_mode, win_event_filter
from .services.themes import (
    THEME_LABELS,
    RETRO_THEME,
    default_theme_for_mode,
    normalize_theme,
    theme_ids_for_mode,
    theme_label,
    theme_palette,
)
from .services.hotkeys_win import HotkeyManager, parse_hotkey
from .services.i18n import (
    LANGUAGE_FLAGS,
    LANGUAGES,
    install_messagebox_translation,
    set_language,
    tr,
    translation_notice,
    translation_source,
)
from .services.streamdeck_bridge import StreamDeckBridge
from .services.streamdeck_installer import open_streamdeck_plugin
from .services.streamdeck_preview import STREAMDECK_ACTION_LABELS, STREAMDECK_PROFILE_LAYOUT, format_character_key
from .services.streamdeck_state import build_streamdeck_windows, reconcile_streamdeck_order
from .services.update_checker import (
    ReleaseInfo,
    UpdateCheckError,
    UpdateCheckResult,
    check_for_update,
    is_automatic_check_due,
    utc_now_iso,
)
from .services.ui_scroll import vertical_scroll_needed, wheel_scroll_units
from .services.configuration_backup import build_configuration_backup, parse_configuration_backup
from .services.diagnostics import (
    build_diagnostic_report,
    format_activity,
    installed_plugin_manifest,
    read_manifest_version,
    read_packaged_plugin_version,
)
from .services.display_overlay import (
    DEFAULT_ROTATION_OVERLAY_LAYOUT,
    build_rotation_displays,
    build_single_display,
    clamp_notification_duration,
    clamp_overlay_opacity,
    normalize_overlay_orientation,
)
from .services.attention_state import WindowAttentionState
from .services.character_visuals import (
    BADGE_CATALOG,
    badge_from_label,
    badge_label,
    bundled_portrait_choices,
    build_avatar_image,
    encode_portrait_file,
    sanitize_character_visuals,
)
from .services.shell_attention_hook import ShellAttentionHook
from .services.tray import TrayController
from .services.windows_startup import set_startup_enabled
from .services.window_order import (
    align_streamdeck_slots_with_managed,
    move_column,
    move_window,
    move_window_by_delta,
    move_window_to_index,
)
from .services.window_table import window_table_values
from .services.win32_enum import get_class_name, get_last_enum_error, get_window_title
from .services.win_event_hook import WinEventHook
from .ui_overlays import OverlayUI

# Optional: Retro in-game popup watcher (requires Windows Graphics Capture)
# This feature can rotate/focus to the character window when a modal popup
# (group invite / exchange request) appears inside the game UI.
try:
    from .retro_popup_watcher import RetroPopupWatcher, WatchedWindow, PopupEvent

    _POPUP_WATCH_AVAILABLE = True
except Exception:
    RetroPopupWatcher = None  # type: ignore
    WatchedWindow = None  # type: ignore
    PopupEvent = None  # type: ignore
    _POPUP_WATCH_AVAILABLE = False

from .storage.settings import (
    DEFAULT_WINDOW_COLUMN_ORDER,
    MODERN_DARK_THEME,
    Settings,
    load_settings,
    save_settings,
)
from .storage.atomic import atomic_write_text
from .storage.profiles import Profile, delete_profile, list_profiles, load_profile, migrate_pickles, save_profile
from .utils.paths import application_dir, ensure_dirs, resource_path
from .utils.logging import AppLogger, install_excepthook


WINDOW_COLUMN_TITLES = {
    "class": "Classe",
    "name": "Nom",
    "alias": "Alias",
    "hwnd": "ID fenêtre",
}
WINDOW_COLUMN_WIDTHS = {
    "class": 105,
    "name": 145,
    "alias": 125,
    "hwnd": 95,
}
OVERLAY_FIELD_LABELS = {
    "none": "Masqué",
    "position": "Numéro",
    "name": "Nom",
    "class": "Classe",
    "alias": "Alias",
}
SWAP_POSITION_LABELS = {
    "top_left": "En haut à gauche",
    "top_center": "En haut au centre",
    "top_right": "En haut à droite",
    "bottom_left": "En bas à gauche",
    "bottom_center": "En bas au centre",
    "bottom_right": "En bas à droite",
}
ROTATION_COALESCE_MS = 18
OFFICIAL_REPOSITORY_URL = (
    "https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay"
)
ANKAMA_ANTI_PHISHING_URL = (
    "https://support.ankama.com/hc/fr/articles/201376953-"
    "Reconna%C3%AEtre-le-phishing-et-s-en-prot%C3%A9ger"
)
LANGUAGE_FLAG_ASSETS = {
    "fr": ("assets", "flags", "fr.png"),
    "en": ("assets", "flags", "en.png"),
    "es": ("assets", "flags", "es.png"),
}


def app_theme_palette(theme_name: str) -> dict[str, str]:
    return theme_palette(theme_name)


def resolved_theme_palette(root, theme_name: str) -> dict[str, str]:
    return app_theme_palette(theme_name)


def blend_hex_colors(foreground: str, background: str, ratio: float) -> str:
    """Blend two #RRGGBB colors; used for a subtle attention pulse."""
    try:
        ratio = max(0.0, min(1.0, float(ratio)))
        fg = tuple(int(foreground[index : index + 2], 16) for index in (1, 3, 5))
        bg = tuple(int(background[index : index + 2], 16) for index in (1, 3, 5))
        mixed = tuple(
            round(a * ratio + b * (1.0 - ratio))
            for a, b in zip(fg, bg, strict=True)
        )
        return "#" + "".join(f"{value:02x}" for value in mixed)
    except (TypeError, ValueError):
        return foreground

# -----------------------
# Dark UI skin (robust)
# -----------------------
def apply_dark_theme(root, theme_name: str = MODERN_DARK_THEME) -> None:
    """Apply one of DWM's built-in Unity or Retro palettes."""
    t = normalize_theme(theme_name)

    style = Style(root)
    try:
        if t not in style.theme_names():
            style.theme_create(t, parent="clam")
        style.theme_use(t)
    except Exception:
        style.theme_use("clam")
    C = app_theme_palette(t)

    try:
        root.configure(bg=C["bg"])
    except Exception:
        pass

    # Classic Tk widgets (Text/Listbox) via option_add so it propagates.
    try:
        root.option_add("*Text.background", C["bg2"])
        root.option_add("*Text.foreground", C["fg"])
        root.option_add("*Text.insertBackground", C["fg"])
        root.option_add("*Text.selectBackground", C["accent"])
        root.option_add("*Text.selectForeground", C["on_accent"])

        root.option_add("*Listbox.background", C["bg2"])
        root.option_add("*Listbox.foreground", C["fg"])
        root.option_add("*Listbox.selectBackground", C["accent"])
        root.option_add("*Listbox.selectForeground", C["on_accent"])

        root.option_add("*Toplevel.background", C["bg"])
    except Exception:
        pass

    # Base style
    style.configure(".",
                    background=C["bg"],
                    foreground=C["fg"],
                    fieldbackground=C["bg2"],
                    bordercolor=C["line"],
                    lightcolor=C["line"],
                    darkcolor=C["line"],
                    troughcolor=C["bg2"],
                    selectbackground=C["accent"],
                    selectforeground=C["on_accent"],
                    font=("Segoe UI", 10),
                    )

    style.configure("TFrame", background=C["bg"])
    style.configure("TLabel", background=C["bg"], foreground=C["fg"])
    style.configure("Header.TLabel", background=C["bg"], foreground=C["accent"], font=("Segoe UI", 16, "bold"))
    style.configure("Muted.TLabel", background=C["bg"], foreground=C["muted"])

    style.configure(
        "TLabelframe",
        background=C["bg"],
        foreground=C["fg"],
        bordercolor=C["line"],
        borderwidth=1,
        relief="solid",
    )
    if t == RETRO_THEME:
        style.configure(
            "TLabelframe.Label",
            background=C["bg3"],
            foreground=C["on_dark"],
            padding=(8, 3),
        )
    else:
        style.configure("TLabelframe.Label", background=C["bg"], foreground=C["fg"])

    style.configure("TButton",
                    background=C["bg3"],
                    foreground=C["on_dark"],
                    borderwidth=1,
                    focusthickness=0,
                    padding=(11, 7))
    style.map("TButton",
              background=[("active", C["button_hover"]), ("pressed", C["bg3"]), ("disabled", C["bg2"])],
              foreground=[("disabled", C["muted"])])
    style.configure("Accent.TButton", background=C["accent"], foreground=C["on_accent"])
    style.map(
        "Accent.TButton",
        background=[("active", C["accent_hover"]), ("pressed", C["accent_pressed"])],
    )
    style.configure(
        "AttentionAction.TButton",
        background=C["attention"],
        foreground=C["on_attention"],
        font=("Segoe UI", 10, "bold"),
    )
    style.map(
        "AttentionAction.TButton",
        background=[
            ("disabled", C["bg3"]),
            ("active", C["attention"]),
            ("pressed", C["attention"]),
        ],
        foreground=[
            ("disabled", C["on_dark"]),
            ("active", C["on_attention"]),
            ("pressed", C["on_attention"]),
        ],
    )
    style.configure(
        "Language.TButton",
        background=C["bg2"],
        foreground=C["fg"],
        padding=(4, 3),
        font=("Segoe UI Emoji", 11),
    )
    style.configure(
        "LanguageActive.TButton",
        background=C["accent"],
        foreground=C["on_accent"],
        padding=(4, 3),
        font=("Segoe UI Emoji", 11),
    )
    style.map(
        "LanguageActive.TButton",
        background=[("active", C["accent_hover"]), ("pressed", C["accent_pressed"])],
    )
    style.configure(
        "StreamDeck.TButton",
        background=C["bg3"],
        foreground=C["on_dark"],
        padding=(6, 9),
        font=("Segoe UI", 9, "bold"),
    )
    style.map(
        "StreamDeck.TButton",
        background=[("active", C["button_hover"]), ("pressed", C["bg3"]), ("disabled", C["bg2"])],
        foreground=[("disabled", C["muted"])],
    )
    style.configure("StreamDeckActive.TButton", background=C["accent"], foreground=C["on_accent"])
    style.map(
        "StreamDeckActive.TButton",
        background=[("active", C["accent_hover"]), ("pressed", C["accent_pressed"])],
    )
    style.configure("StreamDeckIgnored.TButton", background="#4c1d1d", foreground="#fecaca")
    style.map("StreamDeckIgnored.TButton", background=[("active", "#7f1d1d"), ("pressed", "#991b1b")])
    style.configure(
        "StreamDeckAttention.TButton",
        background=C["attention"],
        foreground=C["on_attention"],
    )
    style.map(
        "StreamDeckAttention.TButton",
        background=[("active", C["accent_hover"]), ("pressed", C["accent_pressed"])],
    )

    style.configure("TCheckbutton", background=C["bg"], foreground=C["fg"])
    style.configure("TRadiobutton", background=C["bg"], foreground=C["fg"])

    style.configure("TEntry", fieldbackground=C["bg2"], foreground=C["fg"], insertcolor=C["fg"])
    style.configure("TCombobox", fieldbackground=C["bg2"], background=C["bg2"], foreground=C["fg"])
    style.map("TCombobox",
              fieldbackground=[("readonly", C["bg2"])],
              foreground=[("readonly", C["fg"])])

    style.configure("TNotebook", background=C["bg"], borderwidth=0)
    style.configure("TNotebook.Tab", background=C["bg3"], foreground=C["on_dark"], padding=(10, 6))
    style.map("TNotebook.Tab",
              background=[("selected", C["bg2"]), ("active", C["bg2"])],
              foreground=[("selected", C["fg"]), ("active", C["fg"])])

    style.configure("Treeview",
                    background=C["bg2"],
                    fieldbackground=C["bg2"],
                    foreground=C["fg"],
                    bordercolor=C["line"],
                    rowheight=28)
    style.map("Treeview",
              background=[("selected", C["accent"])],
              foreground=[("selected", C["on_accent"])])
    style.configure("Treeview.Heading", background=C["bg3"], foreground=C["on_dark"], relief="flat")
    style.map("Treeview.Heading", background=[("active", C["button_hover"])])

    style.configure(
        "TScrollbar",
        background=C["bg3"],
        troughcolor=C["bg2"],
        bordercolor=C["bg"],
        arrowcolor=C["on_dark"],
    )


class WindowManagerApp:
    def __init__(self, game_mode: str = "unity", *, start_minimized: bool = False):
        self.dirs = ensure_dirs()
        self.settings_path = self.dirs["root"] / "settings.json"
        self.settings: Settings = load_settings(self.settings_path)
        set_language(self.settings.language)
        install_messagebox_translation(messagebox)

        # Game mode: allow main.py to override, otherwise use last saved setting.
        gm = normalize_game_mode(game_mode, self.settings.game_mode)
        self.game_mode = gm
        self.settings.game_mode = gm
        self.settings.activate_display_preferences(gm)
        self.settings.theme = (self.settings.theme_by_game_mode or {}).get(
            gm,
            default_theme_for_mode(gm),
        )
        self.game_label = game_mode_label(self.game_mode)

        self.logger = AppLogger(
            log_file=self.dirs["logs"] / "app.log",
            actions_file=self.dirs["logs"] / "actions.log",
        )
        install_excepthook(self.logger)

        # Ensure log files exist + useful startup info
        try:
            self.logger.info(
                f"Starting Dofus Window Manager {__version__} ({__release_tag__}) "
                f"| mode={self.game_mode} | data={self.dirs['root']}"
            )
            self.logger.action("App started")
            if not _POPUP_WATCH_AVAILABLE:
                self.logger.warn("PopupWatcher not available (missing windows-capture/numpy or unsupported OS)")
        except Exception:
            pass


        # Migrate legacy pickles if present next to the executable/script.
        legacy_formation = application_dir() / "Formation"
        migrated = migrate_pickles(legacy_formation, self.dirs["profiles"])
        if migrated:
            self.logger.info(f"Migration .pkl -> JSON: {len(migrated)} profil(s) importé(s).")

        # ---- State ----
        self._all_windows: dict[int, GameWindow] = {}
        self._managed_order: list[int] = []  # list of hwnd
        self._ignored: set[int] = set()
        self._streamdeck_order: list[int] = []  # stable slots, including ignored windows
        self._streamdeck_preview_entries: list[dict[str, object]] = []
        self.streamdeck_preview_window: Toplevel | None = None
        self._streamdeck_preview_buttons: dict[int, TtkButton] = {}
        self._streamdeck_preview_poll_job: str | None = None
        self.rotation_index: int = 0
        self._active_game_hwnd: int | None = None
        self._pending_rotation_delta = 0
        self._rotation_request_job: str | None = None
        self.attention_state = WindowAttentionState()
        self._attention_blink_phase = True
        self.aliases: dict[str, str] = {}
        self._active_profile_name = ""
        self._legacy_character_visuals = sanitize_character_visuals(
            self.settings.character_visuals
        )
        self.character_visuals = dict(self._legacy_character_visuals)
        self.desired_order_pseudos: list[str] = []  # current profile order

        # Heuristics (fiabilité)
        self._privilege_mismatch_suspected: bool = False
        self._hotkey_dead_logged: bool = False

        # Window tables and drag/drop state
        self._window_column_order = list(self.settings.window_column_order or DEFAULT_WINDOW_COLUMN_ORDER)
        self._dragged_managed_hwnd: int | None = None
        self._column_drag_tree: Treeview | None = None
        self._column_drag_source: str | None = None
        self._column_drag_target: str | None = None
        self._row_drag_preview_tree: Treeview | None = None
        self._row_drag_preview_item: str | None = None

        # ---- Threading ----
        self._queue: "queue.Queue[object]" = queue.Queue()
        self._stop_event = threading.Event()
        self._refresh_inflight = False
        self._refresh_again_requested = False
        self._update_check_inflight = False
        self._available_release: ReleaseInfo | None = None
        self._scan_revision = 0
        self._game_mode_revision = 0
        self.streamdeck_bridge: StreamDeckBridge | None = None
        self.shell_attention: ShellAttentionHook | None = None
        self._start_minimized = bool(start_minimized)
        self._tray_notice_shown = False
        self.tray = TrayController(resource_path("icons", "dofus.ico"))

        # UI update debounce for event-driven updates
        self._ui_update_pending = False

        # ---- Performance ----
        # Signature of last scanned windows (hwnd+title) to skip unnecessary UI rebuilds.
        self._windows_sig: tuple[tuple[int, str], ...] = tuple()
        # Debounce scan requests (helps when the user clicks refresh multiple times).
        self._last_scan_monotonic: float = 0.0
        self._min_scan_interval_sec: float = 0.35

        # ---- Hotkeys ----
        self.hotkeys = HotkeyManager()

        # ---- UI ----
        self.root = Tk()
        self.root.title(f"Dofus Window Manager {__version__} ({self.game_label})")
        self.root.geometry("1040x760")
        self.root.minsize(900, 620)
        try:
            self.root.iconbitmap(resource_path("icons", "dofus.ico"))
        except Exception:
            pass

        # Apply dark skin (if a dark theme is selected)
        apply_dark_theme(self.root, self.settings.theme)

        self.search_var = StringVar()
        self.game_mode_var = StringVar(value=self.game_label)
        self.game_subtitle_var = StringVar(
            value=tr("Mode {game} · gestion locale des fenêtres", game=self.game_label)
        )
        self.status_var = StringVar(value="")
        self.last_update_time = StringVar(value="")
        self.auto_refresh_enabled = BooleanVar(value=bool(self.settings.auto_refresh))
        self.log_visible = BooleanVar(value=False)
        self.selected_profile = StringVar(value=self.settings.last_profile or "")
        self.overlay_button_text = StringVar(value=tr("Afficher l’overlay"))
        self.next_attention_button_text = StringVar()
        self.character_preview_var = StringVar(value=tr("Sélectionnez un personnage"))
        self._character_preview_photo: ImageTk.PhotoImage | None = None
        self._preview_selected_hwnd: int | None = None

        # Style
        self.style = Style(self.root)
        self.style.theme_use(self.settings.theme)

        if (
            not self.settings.security_notice_accepted
            and not self._show_first_run_security_notice()
        ):
            self.root.destroy()
            raise SystemExit("Avertissement de sécurité non accepté")

        self.hotkeys.start()
        self._build_ui()
        self._localize_ui()
        self.root.after(400, self._localization_tick)
        self.overlay_ui = OverlayUI(
            self.root,
            focus_character=self._focus_from_auxiliary_display,
            save_overlay_position=self._save_overlay_position,
            save_compact_geometry=self._save_compact_geometry,
            save_overlay_size=self._save_overlay_size,
            reorder_character=self._reorder_from_overlay,
            focus_next_attention=lambda: self.focus_next_attention(source="Overlay"),
            palette=resolved_theme_palette(self.root, self.settings.theme),
        )
        self._apply_display_preferences()
        self.update_listboxes()
        self._register_hotkeys()
        self.root.after(1000, self._check_hotkey_errors)
        self.root.after(350, self._poll_active_game_window)
        self.root.after(650, self._attention_blink_tick)

        # Schedule polling of background queue
        self.root.after(100, self._process_queue)

        # Local, loopback-only bridge used by the Stream Deck plugin.
        try:
            bridge = StreamDeckBridge(self._dispatch_streamdeck_command)
            bridge.start()
            self.streamdeck_bridge = bridge
            self._publish_streamdeck_state()
            self._log(f"Stream Deck prêt sur http://127.0.0.1:{bridge.port}")
        except OSError as exc:
            self._log(f"Stream Deck indisponible (port local 32145 occupé) : {exc}")
        except Exception as exc:
            self._log(f"Stream Deck indisponible : {exc}")

        # WinEventHook keeps the registry in sync without polling/scanning.
        self.win_events: WinEventHook | None = None
        self._start_win_event_hook()

        # ---- Optional Retro in-game popup watcher (Groupe/Echange) ----
        # Works best when windows are stacked (off-screen capture via Windows Graphics Capture).
        self.popup_watcher = None
        self._popup_event_pump_started = False
        self._popup_queue = queue.SimpleQueue()
        # Global cooldown to avoid ping-pong when multiple popups are detected at once
        self._popup_global_cooldown_until = 0.0
        self._popup_global_cooldown_sec = float(getattr(self.settings, "popup_watch_global_cooldown_sec", 2.0))
        self._popup_watch_enabled = bool(getattr(self.settings, "popup_watch_enabled", False))

        if self.game_mode == "retro" and _POPUP_WATCH_AVAILABLE and self._popup_watch_enabled:
            try:
                # Emit into a thread-safe queue; handled on the Tk thread.
                self.popup_watcher = RetroPopupWatcher(
                    emit=lambda evt: self._popup_queue.put(evt),
                    max_fps_per_window=4.0,
                    cooldown_sec=2.0,
                )
                self.popup_watcher.set_enabled(self._popup_watch_enabled)
                self._ensure_popup_event_pump()
            except Exception as e:
                try:
                    self.logger.error("PopupWatcher init failed", e)
                except Exception:
                    pass
                self._log(f"PopupWatcher: impossible de démarrer ({e})")
                self.popup_watcher = None


        # Auto refresh timer
        self._schedule_refresh()

        # Initial refresh
        self.refresh_windows()

        # A delayed background check keeps startup responsive and never opens a
        # browser or downloads a file without an explicit user action.
        self.root.after(3000, self._check_updates_on_startup)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        tray_started = self.tray.start(
            show=lambda: self._queue.put(("tray", "show")),
            refresh=lambda: self._queue.put(("tray", "refresh")),
            quit_app=lambda: self._queue.put(("tray", "quit")),
        )
        if self._start_minimized:
            if tray_started:
                self.root.after_idle(self._hide_main_window)
            else:
                self._log("Zone de notification indisponible : l’application reste affichée.")

    # ---------------------------- UI ----------------------------

    def _show_first_run_security_notice(self) -> bool:
        accepted = False
        confirmed = BooleanVar(value=False)
        self.root.withdraw()

        dialog = Toplevel(self.root)
        dialog.title(tr("Avertissement de sécurité"))
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        try:
            dialog.iconbitmap(resource_path("icons", "dofus.ico"))
        except Exception:
            pass

        content = TtkFrame(dialog, padding=18)
        content.pack(fill="both", expand=True)
        TtkLabel(
            content,
            text=tr("Avant d’utiliser Dofus Window Manager"),
            style="Header.TLabel",
        ).pack(anchor="w", pady=(0, 10))
        TtkLabel(
            content,
            text=tr(
                "Téléchargez l’exécutable uniquement depuis les Releases du dépôt GitHub officiel. "
                "Une copie reçue ailleurs peut avoir été modifiée pour contenir un virus, voler vos "
                "identifiants Ankama ou compromettre votre ordinateur."
            ),
            justify="left",
            wraplength=620,
        ).pack(anchor="w")
        TtkButton(
            content,
            text=tr("Ouvrir le dépôt GitHub officiel"),
            command=lambda: webbrowser.open(OFFICIAL_REPOSITORY_URL),
        ).pack(anchor="w", pady=(10, 14))

        TtkLabel(
            content,
            text=tr("Si le fichier provient d’une source non officielle ou vous paraît suspect :"),
            style="Header.TLabel",
        ).pack(anchor="w", pady=(0, 6))
        TtkLabel(
            content,
            text=tr(
                "• Ne l’exécutez pas, ou fermez-le immédiatement et déconnectez le PC du réseau.\n"
                "• Depuis un autre appareil de confiance, changez immédiatement les mots de passe "
                "Ankama et de l’adresse e-mail associée, puis activez la double authentification.\n"
                "• Lancez une analyse complète, idéalement hors ligne, avec Sécurité Windows ou un "
                "antivirus à jour, puis supprimez ou mettez le fichier en quarantaine.\n"
                "• Vérifiez les connexions et activités inhabituelles de vos comptes et contactez le "
                "support concerné en cas de doute."
            ),
            justify="left",
            wraplength=620,
        ).pack(anchor="w", pady=(0, 14))

        confirmation = TtkCheckbutton(
            content,
            text=tr(
                "J’ai lu cet avertissement et je confirme utiliser une copie provenant du dépôt officiel."
            ),
            variable=confirmed,
        )
        confirmation.pack(anchor="w", pady=(0, 14))

        buttons = TtkFrame(content)
        buttons.pack(fill="x")
        continue_button = TtkButton(
            buttons,
            text=tr("Continuer"),
            style="Accent.TButton",
            state="disabled",
        )
        continue_button.pack(side="right")

        def update_continue_state(*_args) -> None:
            continue_button.configure(state="normal" if confirmed.get() else "disabled")

        def accept_notice() -> None:
            nonlocal accepted
            if not confirmed.get():
                return
            self.settings.security_notice_accepted = True
            try:
                save_settings(self.settings_path, self.settings)
            except OSError as exc:
                self.settings.security_notice_accepted = False
                messagebox.showerror(
                    tr("Enregistrement impossible"),
                    str(exc),
                    parent=dialog,
                )
                return
            accepted = True
            dialog.destroy()

        def decline_notice() -> None:
            dialog.destroy()

        continue_button.configure(command=accept_notice)
        confirmed.trace_add("write", update_continue_state)
        TtkButton(buttons, text=tr("Quitter"), command=decline_notice).pack(side="right", padx=(0, 8))
        dialog.protocol("WM_DELETE_WINDOW", decline_notice)
        dialog.update_idletasks()
        x = max(0, (dialog.winfo_screenwidth() - dialog.winfo_reqwidth()) // 2)
        y = max(0, (dialog.winfo_screenheight() - dialog.winfo_reqheight()) // 2)
        dialog.geometry(f"+{x}+{y}")
        dialog.wait_window()
        if accepted:
            self.root.deiconify()
        return accepted

    def _localize_widget_tree(self, widget) -> None:
        try:
            current_title = widget.title()
        except Exception:
            current_title = ""
        title_source = translation_source(current_title)
        if title_source:
            try:
                widget.title(tr(title_source))
            except Exception:
                pass

        try:
            current_text = str(widget.cget("text"))
        except Exception:
            current_text = ""
        text_source = translation_source(current_text)
        if text_source:
            try:
                widget.configure(text=tr(text_source))
            except Exception:
                pass

        try:
            values = tuple(widget.cget("values"))
        except Exception:
            values = ()
        if values:
            translated_values: list[str] = []
            values_changed = False
            for value in values:
                source = translation_source(str(value))
                translated = tr(source) if source else str(value)
                translated_values.append(translated)
                values_changed = values_changed or translated != str(value)
            if values_changed:
                try:
                    widget.configure(values=tuple(translated_values))
                except Exception:
                    pass

        try:
            children = widget.winfo_children()
        except Exception:
            children = ()
        for child in children:
            self._localize_widget_tree(child)

    def _localize_ui(self) -> None:
        self._localize_widget_tree(self.root)
        for tree in (getattr(self, "managed_tree", None), getattr(self, "ignored_tree", None)):
            if tree is None:
                continue
            for column in self._window_column_order:
                tree.heading(column, text=tr(WINDOW_COLUMN_TITLES[column]))
        self.game_subtitle_var.set(
            tr("Mode {game} · gestion locale des fenêtres", game=self.game_label)
        )
        self.overlay_button_text.set(
            tr("Masquer l’overlay")
            if self.settings.rotation_overlay_enabled
            else tr("Afficher l’overlay")
        )
        self._update_next_attention_controls()
        for language, button in getattr(self, "language_buttons", {}).items():
            button.configure(
                style="LanguageActive.TButton" if language == self.settings.language else "Language.TButton"
            )

    def _localization_tick(self) -> None:
        try:
            self._localize_ui()
            self.root.after(400, self._localization_tick)
        except Exception:
            return

    def _attention_color(self) -> str:
        palette = resolved_theme_palette(self.root, self.settings.theme)
        if not self.settings.attention_blink_enabled or self._attention_blink_phase:
            return palette["attention"]
        return blend_hex_colors(palette["attention"], palette["bg2"], 0.68)

    def _apply_attention_blink_visuals(self) -> None:
        color = self._attention_color()
        for tree in (getattr(self, "managed_tree", None), getattr(self, "ignored_tree", None)):
            if tree is not None:
                tree.tag_configure("attention", background=color, foreground="#111827")
        overlay_ui = getattr(self, "overlay_ui", None)
        if overlay_ui is not None:
            overlay_ui.set_attention_blink(
                enabled=self.settings.attention_blink_enabled,
                phase=self._attention_blink_phase,
            )

    def _attention_blink_tick(self) -> None:
        pending = bool(self.attention_state.snapshot())
        if pending and self.settings.attention_blink_enabled:
            self._attention_blink_phase = not self._attention_blink_phase
        else:
            self._attention_blink_phase = True
        self._apply_attention_blink_visuals()
        if pending and self.settings.attention_blink_enabled:
            self._publish_streamdeck_state()
        self.root.after(650, self._attention_blink_tick)

    def _select_language(self, language: str) -> None:
        if language not in LANGUAGES:
            return
        self.settings.language = set_language(language)
        save_settings(self.settings_path, self.settings)
        self._localize_ui()
        self.update_listboxes()
        self._publish_streamdeck_state()
        if language in {"en", "es"}:
            title, notice = translation_notice(language)
            messagebox.showwarning(title, notice, parent=self.root)

    def _load_language_flag_images(self) -> dict[str, ImageTk.PhotoImage]:
        images: dict[str, ImageTk.PhotoImage] = {}
        for language, path_parts in LANGUAGE_FLAG_ASSETS.items():
            try:
                with Image.open(resource_path(*path_parts)) as source:
                    flag = source.convert("RGB")
                    flag.thumbnail((34, 20), Image.Resampling.LANCZOS)
                    images[language] = ImageTk.PhotoImage(flag, master=self.root)
            except Exception:
                continue
        return images

    def _build_ui(self):
        viewport = TtkFrame(self.root)
        viewport.pack(fill="both", expand=True)

        self.main_canvas = Canvas(
            viewport,
            borderwidth=0,
            highlightthickness=0,
            background=self.root.cget("background"),
        )
        self.main_scrollbar = Scrollbar(viewport, orient="vertical", command=self.main_canvas.yview)
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)
        self.main_scrollbar.pack(side="right", fill="y")
        self.main_canvas.pack(side="left", fill="both", expand=True)

        self.main_content = TtkFrame(self.main_canvas)
        self._main_canvas_window = self.main_canvas.create_window((0, 0), window=self.main_content, anchor="nw")
        self.main_content.bind("<Configure>", self._on_main_content_configure)
        self.main_canvas.bind("<Configure>", self._on_main_canvas_configure)
        self.root.bind_all("<MouseWheel>", self._on_global_mousewheel, add="+")

        header = TtkFrame(self.main_content)
        header.pack(fill="x", padx=12, pady=(12, 6))

        title_box = TtkFrame(header)
        title_box.pack(side="left")
        TtkLabel(title_box, text=f"Dofus Window Manager {__version__}", style="Header.TLabel").pack(anchor="w")
        TtkLabel(
            title_box,
            textvariable=self.game_subtitle_var,
            style="Muted.TLabel",
        ).pack(anchor="w")

        language_box = TtkFrame(header)
        language_box.pack(side="right", padx=(10, 0))
        self.language_buttons: dict[str, TtkButton] = {}
        self._language_flag_images = self._load_language_flag_images()
        for language in LANGUAGES:
            flag_image = self._language_flag_images.get(language)
            button = TtkButton(
                language_box,
                text="" if flag_image is not None else LANGUAGE_FLAGS[language],
                image=flag_image or "",
                style="LanguageActive.TButton" if language == self.settings.language else "Language.TButton",
                command=lambda selected=language: self._select_language(selected),
            )
            if flag_image is None:
                button.configure(width=3)
            button.pack(side="left", padx=1)
            self.language_buttons[language] = button

        search_box = TtkFrame(header)
        search_box.pack(side="right", fill="x", expand=True, padx=(30, 0))
        TtkLabel(search_box, text="Rechercher").pack(anchor="w")
        search_row = TtkFrame(search_box)
        search_row.pack(fill="x", pady=(2, 0))
        search = TtkEntry(search_row, textvariable=self.search_var)
        search.pack(side="left", fill="x", expand=True)
        search.bind("<KeyRelease>", lambda e: self.update_listboxes())
        TtkButton(search_row, text="Rafraîchir", command=self.refresh_windows).pack(side="right", padx=(6, 0))

        main = TtkFrame(self.main_content)
        main.pack(fill="both", expand=True, padx=12, pady=(4, 10))
        main.columnconfigure(0, weight=5, minsize=500)
        main.columnconfigure(1, weight=3, minsize=310)
        main.rowconfigure(0, weight=1)

        left = TtkFrame(main)
        left.grid(row=0, column=0, sticky="nsew")

        right = TtkFrame(main)
        right.grid(row=0, column=1, sticky="new", padx=(12, 0))

        # Window tables
        TtkLabel(left, text="Fenêtres gérées").pack(pady=(0, 5), anchor="w")
        self.managed_tree = self._create_window_tree(left, height=10)
        self.managed_tree.bind("<ButtonPress-1>", lambda event: self._on_window_tree_press(event, self.managed_tree), add="+")
        self.managed_tree.bind(
            "<B1-Motion>", lambda event: self._on_window_tree_motion(event, self.managed_tree), add="+"
        )
        self.managed_tree.bind(
            "<ButtonRelease-1>", lambda event: self._on_window_tree_release(event, self.managed_tree), add="+"
        )
        self.managed_tree.bind(
            "<<TreeviewSelect>>",
            lambda _event: self._on_character_tree_selected(self.managed_tree),
            add="+",
        )
        TtkLabel(
            left,
            text="Glissez un personnage pour modifier l’ordre ; glissez un en-tête pour déplacer une colonne.",
        ).pack(pady=(4, 0), anchor="w")

        TtkLabel(left, text="Fenêtres ignorées").pack(pady=(10, 5), anchor="w")
        self.ignored_tree = self._create_window_tree(left, height=5)
        self.ignored_tree.bind("<ButtonPress-1>", lambda event: self._on_window_tree_press(event, self.ignored_tree), add="+")
        self.ignored_tree.bind(
            "<B1-Motion>", lambda event: self._on_window_tree_motion(event, self.ignored_tree), add="+"
        )
        self.ignored_tree.bind(
            "<ButtonRelease-1>", lambda event: self._on_window_tree_release(event, self.ignored_tree), add="+"
        )
        self.ignored_tree.bind(
            "<<TreeviewSelect>>",
            lambda _event: self._on_character_tree_selected(self.ignored_tree),
            add="+",
        )

        # Right panel controls, grouped by frequency and purpose.
        navigation = TtkLabelFrame(right, text="Navigation", padding=8)
        navigation.pack(fill="x", pady=(0, 8))
        navigation.columnconfigure(0, weight=1)
        navigation.columnconfigure(1, weight=1)
        TtkButton(navigation, text="← Précédent", command=lambda: self.request_rotation("backward")).grid(
            row=0, column=0, sticky="ew", padx=(0, 3), pady=2
        )
        TtkButton(navigation, text="Suivant →", command=lambda: self.request_rotation("forward")).grid(
            row=0, column=1, sticky="ew", padx=(3, 0), pady=2
        )
        TtkButton(navigation, text="↑ Monter", command=lambda: self.move_selected(-1)).grid(
            row=1, column=0, sticky="ew", padx=(0, 3), pady=2
        )
        TtkButton(navigation, text="↓ Descendre", command=lambda: self.move_selected(1)).grid(
            row=1, column=1, sticky="ew", padx=(3, 0), pady=2
        )
        self.next_attention_button = TtkButton(
            navigation,
            textvariable=self.next_attention_button_text,
            command=lambda: self.focus_next_attention(source="Application"),
            style="AttentionAction.TButton",
        )
        self.next_attention_button.grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(5, 2)
        )

        selection = TtkLabelFrame(right, text="Fenêtre sélectionnée", padding=8)
        selection.pack(fill="x", pady=(0, 8))
        selection.columnconfigure(0, weight=1)
        selection.columnconfigure(1, weight=1)
        character_preview = TtkFrame(selection)
        character_preview.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        preview_holder = TtkFrame(character_preview, width=72, height=72)
        preview_holder.pack(side="left", padx=(0, 8))
        preview_holder.pack_propagate(False)
        self.character_preview_image = TkLabel(
            preview_holder,
            borderwidth=0,
        )
        self.character_preview_image.pack(fill="both", expand=True)
        TtkLabel(
            character_preview,
            textvariable=self.character_preview_var,
            justify="left",
            wraplength=160,
        ).pack(side="left", fill="x", expand=True)
        TtkButton(selection, text="Personnaliser…", command=self.open_character_customization).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=2
        )
        TtkLabel(
            selection,
            text=(
                "Astuce : un élément (Terre, Feu, Eau, Air) ou un métier peut servir d’alias "
                "pour distinguer des pseudos proches ou deux personnages de même classe."
            ),
            style="Muted.TLabel",
            wraplength=235,
            justify="left",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 7))
        TtkButton(selection, text="Ignorer", command=self.ignore_selected).grid(
            row=3, column=0, sticky="ew", padx=(0, 3), pady=2
        )
        TtkButton(selection, text="Réintégrer", command=self.unignore_selected).grid(
            row=3, column=1, sticky="ew", padx=(3, 0), pady=2
        )

        profiles = TtkLabelFrame(right, text="Profils", padding=8)
        profiles.pack(fill="x", pady=(0, 8))
        profiles.columnconfigure(0, weight=1)
        profiles.columnconfigure(1, weight=1)
        self.profile_combo = Combobox(
            profiles,
            textvariable=self.selected_profile,
            values=self._get_profiles(),
            state="readonly",
        )
        self.profile_combo.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        TtkButton(profiles, text="Charger", command=self.load_profile_selected).grid(
            row=1, column=0, sticky="ew", padx=(0, 3), pady=2
        )
        TtkButton(profiles, text="Enregistrer…", command=self.save_profile_dialog).grid(
            row=1, column=1, sticky="ew", padx=(3, 0), pady=2
        )
        TtkButton(profiles, text="Gérer les profils…", command=self.open_profile_manager).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=2
        )

        application = TtkLabelFrame(right, text="Application", padding=8)
        application.pack(fill="x")
        mode_row = TtkFrame(application)
        mode_row.pack(fill="x", pady=(1, 6))
        TtkLabel(mode_row, text="Version de Dofus").pack(side="left")
        self.game_mode_combo = Combobox(
            mode_row,
            textvariable=self.game_mode_var,
            values=("Unity", "Retro"),
            state="readonly",
            width=9,
        )
        self.game_mode_combo.pack(side="right")
        self.game_mode_combo.bind("<<ComboboxSelected>>", self._on_game_mode_selected)
        TtkButton(application, text="Paramètres…", command=self.open_settings_window).pack(fill="x", pady=2)
        TtkButton(
            application,
            text="Réinitialiser l’affichage…",
            command=self.reset_display_settings,
        ).pack(fill="x", pady=2)
        display_row = TtkFrame(application)
        display_row.pack(fill="x", pady=2)
        TtkButton(display_row, text="Mode compact", command=self.open_compact_mode).pack(
            side="left", fill="x", expand=True, padx=(0, 3)
        )
        TtkButton(
            display_row,
            textvariable=self.overlay_button_text,
            command=self.toggle_rotation_overlay,
        ).pack(side="left", fill="x", expand=True, padx=(3, 0))
        TtkButton(application, text="Aperçu Stream Deck…", command=self.open_streamdeck_preview).pack(fill="x", pady=2)
        TtkButton(application, text="Diagnostic…", command=self.open_diagnostics_window).pack(fill="x", pady=2)
        TtkButton(
            application,
            text="Sauvegarder / restaurer…",
            command=self.open_configuration_manager,
        ).pack(fill="x", pady=2)
        TtkButton(
            application,
            text="Installer le plugin Stream Deck",
            command=self.install_streamdeck_plugin,
            style="Accent.TButton",
        ).pack(fill="x", pady=2)
        TtkButton(
            application,
            text="Dépôt GitHub officiel",
            command=lambda: self._open_trusted_web_page(
                OFFICIAL_REPOSITORY_URL,
                "Dépôt GitHub officiel",
            ),
        ).pack(fill="x", pady=2)
        TtkButton(
            application,
            text="Conseils anti-phishing Ankama",
            command=lambda: self._open_trusted_web_page(
                ANKAMA_ANTI_PHISHING_URL,
                "Conseils anti-phishing Ankama",
            ),
        ).pack(fill="x", pady=2)
        self.update_button = TtkButton(
            application,
            text="Rechercher une mise à jour…",
            command=self.check_for_updates,
        )
        self.update_button.pack(fill="x", pady=2)
        TtkLabel(
            application,
            text="Illustrations et icônes Dofus © Ankama Games. Projet communautaire non affilié.",
            style="Muted.TLabel",
            wraplength=235,
            justify="left",
        ).pack(fill="x", pady=(7, 1))
        TtkButton(application, text="Quitter", command=lambda: self.on_close(force=True)).pack(fill="x", pady=2)

        # Status and logs
        bottom = TtkFrame(self.main_content)
        bottom.pack(fill="both", expand=False, padx=12, pady=(0, 10))

        status_row = TtkFrame(bottom)
        status_row.pack(fill="x")
        TtkLabel(status_row, textvariable=self.status_var).pack(side="left", anchor="w")
        TtkCheckbutton(
            status_row,
            text="Afficher le journal",
            variable=self.log_visible,
            command=self._toggle_log_visibility,
        ).pack(side="right")

        self.log_text = Text(bottom, height=7)
        self.log_text.pack(fill="both", expand=True, pady=(5, 5))
        self.log_text.pack_forget()

        self.log_footer = TtkFrame(bottom)
        self.log_footer.pack(fill="x", pady=(4, 0))
        TtkCheckbutton(
            self.log_footer,
            text="Actualisation automatique",
            variable=self.auto_refresh_enabled,
            command=self._on_toggle_autorefresh,
        ).pack(side="left")
        TtkLabel(self.log_footer, textvariable=self.last_update_time, style="Muted.TLabel").pack(side="right")

    def _on_main_content_configure(self, _event=None) -> None:
        bounds = self.main_canvas.bbox("all")
        if bounds is not None:
            self.main_canvas.configure(scrollregion=bounds)

    def _on_main_canvas_configure(self, event) -> None:
        self.main_canvas.itemconfigure(self._main_canvas_window, width=event.width)

    def _on_global_mousewheel(self, event):
        widget = self.root.winfo_containing(event.x_root, event.y_root)
        current = widget
        inside_main_content = False
        while current is not None:
            if current is self.main_content:
                inside_main_content = True
            if isinstance(current, Treeview):
                first, last = current.yview()
                if vertical_scroll_needed(first, last):
                    return None
            elif isinstance(current, Text):
                return None
            current = getattr(current, "master", None)

        if not inside_main_content:
            return None

        units = wheel_scroll_units(event.delta)
        first, last = self.main_canvas.yview()
        if units and vertical_scroll_needed(first, last):
            self.main_canvas.yview_scroll(units, "units")
            return "break"
        return None

    def _toggle_log_visibility(self) -> None:
        if self.log_visible.get():
            self.log_text.pack(fill="both", expand=True, pady=(5, 5), before=self.log_footer)
        else:
            self.log_text.pack_forget()

    def _create_window_tree(self, parent, *, height: int) -> Treeview:
        container = TtkFrame(parent)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        tree = Treeview(
            container,
            columns=DEFAULT_WINDOW_COLUMN_ORDER,
            displaycolumns=self._window_column_order,
            show="headings",
            selectmode="browse",
            height=height,
        )
        vertical_scrollbar = Scrollbar(container, orient="vertical", command=tree.yview)
        horizontal_scrollbar = Scrollbar(container, orient="horizontal", command=tree.xview)
        tree.configure(
            yscrollcommand=vertical_scrollbar.set,
            xscrollcommand=horizontal_scrollbar.set,
        )
        tree.grid(row=0, column=0, sticky="nsew")
        vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        horizontal_scrollbar.grid(row=1, column=0, sticky="ew")

        for column in DEFAULT_WINDOW_COLUMN_ORDER:
            tree.heading(column, text=WINDOW_COLUMN_TITLES[column])
            tree.column(
                column,
                width=WINDOW_COLUMN_WIDTHS[column],
                minwidth=70,
                anchor="center" if column in {"class", "hwnd"} else "w",
                stretch=column in {"name", "alias"},
            )
        tree.tag_configure("active", foreground="#5eead4")
        tree.tag_configure("attention", background=self._attention_color(), foreground="#111827")
        tree.tag_configure("empty", foreground=resolved_theme_palette(self.root, self.settings.theme)["muted"])
        tree.tag_configure("drop_before", background="#164e63", foreground="#ffffff")
        tree.tag_configure("drop_after", background="#155e75", foreground="#ffffff")
        return tree

    def _display_column_at(self, tree: Treeview, x: int) -> str | None:
        right_edge = 0
        for column in self._window_column_order:
            right_edge += int(tree.column(column, "width"))
            if x < right_edge:
                return column
        return None

    def _on_window_tree_press(self, event, tree: Treeview):
        self._clear_drag_previews()
        region = tree.identify_region(event.x, event.y)
        self._column_drag_tree = None
        self._column_drag_source = None
        self._dragged_managed_hwnd = None

        if region == "heading":
            column = self._display_column_at(tree, event.x)
            if column:
                self._column_drag_tree = tree
                self._column_drag_source = column
                self._set_drag_cursor(tree, "sb_h_double_arrow")
                self._update_column_drag_preview(tree, column)
            return

        if tree is self.managed_tree and region in {"cell", "tree"}:
            row = tree.identify_row(event.y)
            if row:
                try:
                    self._dragged_managed_hwnd = int(row)
                except ValueError:
                    return
                tree.selection_set(row)
                self._set_drag_cursor(tree, "hand2")

    @staticmethod
    def _set_drag_cursor(tree: Treeview, cursor: str) -> None:
        try:
            tree.configure(cursor=cursor)
        except Exception:
            tree.configure(cursor="hand2" if cursor else "")

    def _clear_column_drag_preview(self) -> None:
        tree = self._column_drag_tree
        if tree is not None:
            for column in DEFAULT_WINDOW_COLUMN_ORDER:
                tree.heading(column, text=WINDOW_COLUMN_TITLES[column])
            self._set_drag_cursor(tree, "")
        self._column_drag_target = None

    def _update_column_drag_preview(self, tree: Treeview, target: str | None) -> None:
        source = self._column_drag_source
        if self._column_drag_tree is not tree or source is None:
            return
        for column in DEFAULT_WINDOW_COLUMN_ORDER:
            tree.heading(column, text=WINDOW_COLUMN_TITLES[column])
        tree.heading(source, text=f"↔ {WINDOW_COLUMN_TITLES[source]}")
        self._column_drag_target = target
        if target and target != source:
            tree.heading(target, text=f"▸ {WINDOW_COLUMN_TITLES[target]}")
            self.status_var.set(
                f"Déposer « {WINDOW_COLUMN_TITLES[source]} » avant « {WINDOW_COLUMN_TITLES[target]} »."
            )
        else:
            self.status_var.set(f"Déplacement de la colonne « {WINDOW_COLUMN_TITLES[source]} »…")

    def _clear_row_drag_preview(self) -> None:
        tree = self._row_drag_preview_tree
        item = self._row_drag_preview_item
        if tree is not None and item and tree.exists(item):
            tags = tuple(tag for tag in tree.item(item, "tags") if tag not in {"drop_before", "drop_after"})
            tree.item(item, tags=tags)
        if tree is not None:
            self._set_drag_cursor(tree, "")
        self._row_drag_preview_tree = None
        self._row_drag_preview_item = None

    def _update_row_drag_preview(self, tree: Treeview, target: str, *, after: bool) -> None:
        self._clear_row_drag_preview()
        if target == str(self._dragged_managed_hwnd) or not tree.exists(target):
            self._set_drag_cursor(tree, "hand2")
            return
        preview_tag = "drop_after" if after else "drop_before"
        tags = tuple(tag for tag in tree.item(target, "tags") if tag not in {"drop_before", "drop_after"})
        tree.item(target, tags=(*tags, preview_tag))
        self._row_drag_preview_tree = tree
        self._row_drag_preview_item = target
        self._set_drag_cursor(tree, "hand2")
        try:
            target_hwnd = int(target)
        except ValueError:
            return
        window = self._all_windows.get(target_hwnd)
        name = (self.aliases.get(window.pseudo) or window.pseudo) if window else target
        placement = "après" if after else "avant"
        self.status_var.set(f"Déposer le personnage {placement} « {name} ».")

    def _clear_drag_previews(self) -> None:
        self._clear_row_drag_preview()
        self._clear_column_drag_preview()

    def _on_window_tree_motion(self, event, tree: Treeview):
        if self._column_drag_tree is tree and self._column_drag_source:
            self._update_column_drag_preview(tree, self._display_column_at(tree, event.x))
            return
        if tree is not self.managed_tree or self._dragged_managed_hwnd is None:
            return
        if event.y < 22:
            tree.yview_scroll(-1, "units")
        elif event.y > tree.winfo_height() - 22:
            tree.yview_scroll(1, "units")
        target = tree.identify_row(event.y)
        if not target:
            self._clear_row_drag_preview()
            self._set_drag_cursor(tree, "hand2")
            return
        bounds = tree.bbox(target)
        after = bool(bounds and event.y >= bounds[1] + bounds[3] / 2)
        self._update_row_drag_preview(tree, target, after=after)

    def _on_window_tree_release(self, event, tree: Treeview):
        if self._column_drag_tree is tree and self._column_drag_source:
            target_column = self._display_column_at(tree, event.x)
            source_column = self._column_drag_source
            self._clear_drag_previews()
            self._column_drag_tree = None
            self._column_drag_source = None
            if target_column and target_column != source_column:
                order = move_column(self._window_column_order, source_column, target_column)
                self._apply_window_column_order(order, persist=True)
                self._log("Ordre des colonnes modifié")
            return

        dragged_hwnd = self._dragged_managed_hwnd
        target = tree.identify_row(event.y)
        bounds = tree.bbox(target) if target else ()
        after = bool(bounds and event.y >= bounds[1] + bounds[3] / 2)
        self._clear_drag_previews()
        self._set_drag_cursor(tree, "")
        self._dragged_managed_hwnd = None
        if tree is not self.managed_tree or dragged_hwnd is None:
            return
        if self.search_var.get().strip():
            self._log("Glisser-déposer désactivé pendant un filtrage.")
            self.update_listboxes()
            return

        if not target:
            return
        try:
            target_hwnd = int(target)
        except ValueError:
            return
        self._move_managed_window(dragged_hwnd, target_hwnd, after=after)

    def _apply_window_column_order(self, order: list[str], *, persist: bool) -> None:
        normalized = [column for column in order if column in DEFAULT_WINDOW_COLUMN_ORDER]
        for column in DEFAULT_WINDOW_COLUMN_ORDER:
            if column not in normalized:
                normalized.append(column)
        self._window_column_order = normalized
        self.managed_tree.configure(displaycolumns=normalized)
        self.ignored_tree.configure(displaycolumns=normalized)
        if persist:
            self.settings.window_column_order = list(normalized)
            save_settings(self.settings_path, self.settings)

    def _log(self, msg: str):
        self.status_var.set(msg)
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        # keep it light
        if int(self.log_text.index("end-1c").split(".")[0]) > 250:
            self.log_text.delete("1.0", "80.0")
        self.logger.action(msg)

    # ---------------------------- Compact mode and overlays ----------------------------

    def _active_character_visuals(self) -> dict[str, dict[str, str]]:
        visuals = getattr(self, "character_visuals", None)
        if visuals is not None:
            return visuals
        return sanitize_character_visuals(
            getattr(getattr(self, "settings", None), "character_visuals", None)
        )

    def _rotation_display_entries(self):
        active_hwnd = self._active_game_hwnd
        if active_hwnd not in self._all_windows and self._managed_order:
            self.rotation_index %= len(self._managed_order)
            active_hwnd = self._managed_order[self.rotation_index]
        return build_rotation_displays(
            self._all_windows,
            self._managed_order,
            self.aliases,
            active_hwnd,
            self.attention_state.queue(),
            self._active_character_visuals(),
        )

    def _refresh_auxiliary_displays(self) -> None:
        overlay_ui = getattr(self, "overlay_ui", None)
        if overlay_ui is not None:
            overlay_ui.update_characters(
                self._rotation_display_entries(),
                attention_count=len(self.attention_state.queue()),
            )

    def _apply_display_preferences(self) -> None:
        overlay_ui = getattr(self, "overlay_ui", None)
        if overlay_ui is None:
            return
        overlay_ui.set_palette(resolved_theme_palette(self.root, self.settings.theme))
        overlay_ui.set_attention_blink(
            enabled=self.settings.attention_blink_enabled,
            phase=self._attention_blink_phase,
        )
        overlay_ui.configure_persistent(
            enabled=self.settings.rotation_overlay_enabled,
            x=self.settings.rotation_overlay_x,
            y=self.settings.rotation_overlay_y,
            opacity=self.settings.rotation_overlay_opacity,
            locked=self.settings.rotation_overlay_locked,
            layout=self.settings.rotation_overlay_layout,
            orientation=self.settings.rotation_overlay_orientation,
            width=self.settings.rotation_overlay_width,
            auto_width=self.settings.rotation_overlay_auto_width,
            height=self.settings.rotation_overlay_height,
            show_portrait=self.settings.show_overlay_portraits,
            show_badge=self.settings.show_overlay_badges,
        )
        self.overlay_button_text.set(
            tr("Masquer l’overlay") if self.settings.rotation_overlay_enabled else tr("Afficher l’overlay")
        )
        self._refresh_auxiliary_displays()

    def _apply_runtime_theme(self, theme_name: str) -> None:
        theme = normalize_theme(theme_name, self.game_mode)
        apply_dark_theme(self.root, theme)
        self.settings.theme = theme
        self.settings.theme_by_game_mode[self.game_mode] = theme
        palette = resolved_theme_palette(self.root, theme)
        self.root.configure(background=palette["bg"])
        self.main_canvas.configure(background=palette["bg"])
        self.log_text.configure(
            background=palette["bg2"],
            foreground=palette["fg"],
            insertbackground=palette["fg"],
            selectbackground=palette["accent"],
        )
        for tree in (getattr(self, "managed_tree", None), getattr(self, "ignored_tree", None)):
            if tree is not None:
                tree.tag_configure("empty", foreground=palette["muted"])
        overlay_ui = getattr(self, "overlay_ui", None)
        if overlay_ui is not None:
            overlay_ui.set_palette(palette)

    def open_compact_mode(self) -> None:
        self._refresh_auxiliary_displays()
        self.overlay_ui.open_compact(self.settings.compact_window_geometry)

    def toggle_rotation_overlay(self) -> None:
        self.settings.rotation_overlay_enabled = not self.settings.rotation_overlay_enabled
        save_settings(self.settings_path, self.settings)
        self._apply_display_preferences()
        state = "affiché" if self.settings.rotation_overlay_enabled else "masqué"
        self._log(f"Overlay de rotation {state}")

    def _save_overlay_position(self, x: int, y: int) -> None:
        if (x, y) == (self.settings.rotation_overlay_x, self.settings.rotation_overlay_y):
            return
        self.settings.rotation_overlay_x = int(x)
        self.settings.rotation_overlay_y = int(y)
        save_settings(self.settings_path, self.settings)

    def _save_overlay_size(self, width: int, height: int, *, auto_width: bool = False) -> None:
        normalized = (max(80, min(1800, int(width))), max(80, min(1600, int(height))))
        if (*normalized, bool(auto_width)) == (
            self.settings.rotation_overlay_width,
            self.settings.rotation_overlay_height,
            self.settings.rotation_overlay_auto_width,
        ):
            return
        self.settings.rotation_overlay_width, self.settings.rotation_overlay_height = normalized
        self.settings.rotation_overlay_auto_width = bool(auto_width)
        save_settings(self.settings_path, self.settings)

    def _reorder_from_overlay(self, hwnd: int, destination: str | int) -> None:
        if hwnd not in self._managed_order:
            return
        active_hwnd = self._active_game_hwnd
        if isinstance(destination, str):
            if destination not in {"up", "down"}:
                return
            delta = -1 if destination == "up" else 1
            new_order = move_window_by_delta(self._managed_order, hwnd, delta)
        else:
            new_order = move_window_to_index(self._managed_order, hwnd, destination)
        if new_order == self._managed_order:
            return
        self._managed_order = new_order
        if active_hwnd in self._managed_order:
            self.rotation_index = self._managed_order.index(active_hwnd)
        self._publish_order_consumers()
        self.update_listboxes(publish_consumers=False)
        window = self._all_windows.get(hwnd)
        if window is not None:
            self._log(
                f"Overlay : {window.pseudo} déplacé en position "
                f"{self._managed_order.index(hwnd) + 1}"
            )

    def _save_compact_geometry(self, geometry: str) -> None:
        value = (geometry or "").strip()
        if not value or value == self.settings.compact_window_geometry:
            return
        self.settings.compact_window_geometry = value
        save_settings(self.settings_path, self.settings)

    def _record_character_focus(self, hwnd: int, *, notify: bool) -> None:
        previous_hwnd = self._active_game_hwnd
        self._active_game_hwnd = hwnd
        attention_cleared = self.attention_state.clear(hwnd)
        if hwnd in self._managed_order:
            self.rotation_index = self._managed_order.index(hwnd)
        if attention_cleared:
            self.update_listboxes()
        elif previous_hwnd != hwnd:
            self._refresh_focus_views()
        if not notify or not self.settings.swap_notification_enabled:
            return
        window = self._all_windows.get(hwnd)
        if window is None:
            return
        entry = build_single_display(
            window,
            aliases=self.aliases,
            managed_order=self._managed_order,
            active=True,
            attention=False,
            appearance=self._active_character_visuals().get(window.pseudo),
        )
        self.overlay_ui.show_swap_notification(
            entry,
            anchor=self.settings.swap_notification_anchor,
            duration_ms=self.settings.swap_notification_duration_ms,
            opacity=self.settings.swap_notification_opacity,
            layout=self.settings.swap_notification_layout,
            show_portrait=self.settings.show_popup_portraits,
            show_badge=self.settings.show_popup_badges,
        )

    def _focus_from_auxiliary_display(self, hwnd: int) -> None:
        window = self._all_windows.get(hwnd)
        if window is None or not is_window(hwnd):
            self._log("La fenêtre sélectionnée n’est plus disponible.")
            self.refresh_windows(quiet=True, force=True)
            return
        try:
            focus_hwnd(hwnd)
        except FocusError as exc:
            self._log(f"Focus échoué depuis le mode compact ou l’overlay : {exc}")
            return
        self._record_character_focus(hwnd, notify=True)
        self._log(f"Mode compact / overlay → {window.title}")

    def focus_managed_position(self, position: int) -> bool:
        try:
            index = int(position) - 1
        except (TypeError, ValueError):
            return False
        if index < 0 or index >= len(self._managed_order):
            self._log(f"Raccourci fenêtre {index + 1} : aucune fenêtre à cette position")
            return False
        hwnd = self._managed_order[index]
        self.rotation_index = index
        self._focus_from_auxiliary_display(hwnd)
        return True

    def _activate_next_attention(self, *, source: str) -> dict[str, object]:
        """Focus the oldest valid request and clear it only after focus succeeds."""
        discarded_stale = False
        while True:
            hwnd = self.attention_state.next()
            if hwnd is None:
                if discarded_stale:
                    self.update_listboxes()
                else:
                    self._update_next_attention_controls()
                return {
                    "ok": False,
                    "error": "Aucune fenêtre ne demande votre attention.",
                    "_status": 404,
                }

            window = self._all_windows.get(hwnd)
            if window is None or not is_window(hwnd):
                self.attention_state.clear(hwnd)
                discarded_stale = True
                continue

            try:
                focus_hwnd(hwnd)
            except FocusError as exc:
                self._log(f"{source}, prochaine alerte : focus échoué ({exc})")
                return {"ok": False, "error": str(exc), "_status": 409}

            self._record_character_focus(hwnd, notify=True)
            remaining = len(self.attention_state.queue())
            name = self.aliases.get(window.pseudo) or window.pseudo
            self._log(f"{source}, prochaine alerte → {window.title}")
            return {
                "ok": True,
                "hwnd": hwnd,
                "name": name,
                "remaining": remaining,
            }

    def focus_next_attention(self, *, source: str = "Application") -> bool:
        return bool(self._activate_next_attention(source=source).get("ok"))

    def _update_next_attention_controls(self) -> None:
        count = len(self.attention_state.queue())
        variable = getattr(self, "next_attention_button_text", None)
        if variable is not None:
            variable.set(tr("⚠ Prochaine alerte ({count})", count=count))
        button = getattr(self, "next_attention_button", None)
        if button is not None:
            button.configure(state=("normal" if count else "disabled"))

    def _poll_active_game_window(self) -> None:
        if self._stop_event.is_set():
            return
        overlay_ui = getattr(self, "overlay_ui", None)
        if overlay_ui is not None and overlay_ui.has_visible_character_list:
            foreground_hwnd = get_foreground_hwnd()
            if foreground_hwnd in self._all_windows and foreground_hwnd != self._active_game_hwnd:
                self._record_character_focus(foreground_hwnd, notify=False)
        self.root.after(350, self._poll_active_game_window)

    # ---------------------------- Updates ----------------------------

    def _check_updates_on_startup(self) -> None:
        if not self.settings.check_updates_automatically:
            return
        if not is_automatic_check_due(self.settings.last_update_check_at):
            return
        self._start_update_check(manual=False)

    def check_for_updates(self) -> None:
        self._start_update_check(manual=True)

    def _start_update_check(self, *, manual: bool) -> None:
        if self._stop_event.is_set():
            return
        if self._update_check_inflight:
            if manual:
                messagebox.showinfo(
                    "Mise à jour",
                    "Une recherche est déjà en cours.",
                    parent=self.root,
                )
            return

        self._update_check_inflight = True
        self.update_button.configure(text="Recherche en cours…", style="TButton")
        self.update_button.state(["disabled"])
        if manual:
            self._log("Recherche d’une mise à jour sur le dépôt officiel…")

        include_prereleases = bool(self.settings.include_prereleases)

        def worker() -> None:
            checked_at = utc_now_iso()
            try:
                result = check_for_update(
                    __release_tag__,
                    include_prereleases=include_prereleases,
                )
                self._queue.put(("update_check", manual, result, "", checked_at))
            except UpdateCheckError as exc:
                self._queue.put(("update_check", manual, None, str(exc), checked_at))
            except Exception:
                self._queue.put(
                    (
                        "update_check",
                        manual,
                        None,
                        "La recherche de mise à jour a échoué de manière inattendue.",
                        checked_at,
                    )
                )

        threading.Thread(target=worker, name="DWMUpdateCheck", daemon=True).start()

    def _finish_update_check(
        self,
        *,
        manual: bool,
        result: UpdateCheckResult | None,
        error: str,
        checked_at: str,
    ) -> None:
        self._update_check_inflight = False
        self.update_button.state(["!disabled"])
        self.settings.last_update_check_at = checked_at
        try:
            save_settings(self.settings_path, self.settings)
        except OSError as exc:
            self.logger.warn(f"Update check timestamp could not be saved: {exc}")

        if error:
            self._restore_update_button()
            self.logger.warn(f"Update check failed: {error}")
            if manual:
                self._log(f"Mise à jour : {error}")
                messagebox.showwarning("Mise à jour", error, parent=self.root)
            return

        if result is None:
            self._restore_update_button()
            return

        release = result.latest_release
        if result.update_available and release is not None:
            self._available_release = release
            self._restore_update_button()
            self._log(f"Mise à jour {release.tag} disponible sur le dépôt officiel")
            if manual:
                self._offer_official_release(release)
            return

        self._available_release = None
        self._restore_update_button()
        self._log(f"Dofus Window Manager est à jour ({__release_tag__})")
        if manual:
            if release is None:
                detail = "Aucune version publiée compatible n’a été trouvée."
            else:
                detail = f"Vous utilisez déjà la version la plus récente ({__release_tag__})."
            messagebox.showinfo("Mise à jour", detail, parent=self.root)

    def _restore_update_button(self) -> None:
        if self._available_release is None:
            self.update_button.configure(text="Rechercher une mise à jour…", style="TButton")
            return
        self.update_button.configure(
            text=f"Mise à jour {self._available_release.tag} disponible…",
            style="Accent.TButton",
        )

    def _offer_official_release(self, release: ReleaseInfo) -> None:
        release_label = release.tag
        if release.name and release.name != release.tag:
            release_label = f"{release.tag} — {release.name}"
        open_release = messagebox.askyesno(
            "Mise à jour disponible",
            (
                f"Version installée : {__version__} ({__release_tag__})\n"
                f"Nouvelle version : {release_label}\n\n"
                "Aucun fichier ne sera téléchargé automatiquement. "
                "Ouvrir la Release officielle dans votre navigateur ?"
            ),
            parent=self.root,
        )
        if not open_release:
            return
        try:
            opened = webbrowser.open(release.url, new=2)
        except Exception as exc:
            opened = False
            self.logger.warn(f"Official release page could not be opened: {exc}")
        if not opened:
            messagebox.showwarning(
                "Mise à jour",
                "Le navigateur n’a pas pu être ouvert. Consultez la Release depuis le dépôt officiel.",
                parent=self.root,
            )

    def _open_trusted_web_page(self, url: str, label: str) -> None:
        try:
            opened = webbrowser.open(url, new=2)
        except Exception as exc:
            opened = False
            self.logger.warn(f"Trusted web page could not be opened ({label}): {exc}")
        if opened:
            self._log(f"Ouverture : {label}")
            return
        messagebox.showwarning(
            "Lien externe",
            tr(
                "Le navigateur n’a pas pu être ouvert.\n\nAdresse à consulter :\n{url}",
                url=url,
            ),
            parent=self.root,
        )

    # ---------------------------- Profiles ----------------------------

    def _get_profiles(self):
        return list_profiles(self.dirs["profiles"])

    def _refresh_profile_combo(self):
        self.profile_combo["values"] = self._get_profiles()

    def _apply_loaded_profile(self, profile: Profile, *, migrate_legacy: bool = True) -> None:
        self._active_profile_name = profile.name
        self.aliases.clear()
        self.aliases.update(
            {pseudo: alias.strip() for pseudo, alias in profile.aliases.items() if alias.strip()}
        )
        if profile.visuals is None:
            self.character_visuals = dict(self._legacy_character_visuals)
            if migrate_legacy:
                profile.visuals = dict(self.character_visuals)
                profile.game_mode = profile.game_mode or self.game_mode
                try:
                    save_profile(self.dirs["profiles"], profile)
                except OSError:
                    pass
        else:
            self.character_visuals = sanitize_character_visuals(profile.visuals)
        self.desired_order_pseudos = list(profile.order)

    def _save_active_profile_customizations(self) -> bool:
        """Persist aliases and appearances without changing the saved window order."""
        name = self._active_profile_name.strip()
        if not name:
            return False
        try:
            profile = load_profile(self.dirs["profiles"], name)
        except Exception:
            return False
        profile.aliases = {
            pseudo: alias.strip() for pseudo, alias in self.aliases.items() if alias.strip()
        }
        profile.visuals = sanitize_character_visuals(self.character_visuals)
        profile.game_mode = self.game_mode
        try:
            save_profile(self.dirs["profiles"], profile)
        except OSError:
            return False
        return True

    def save_profile_dialog(self):
        current_name = self.selected_profile.get().strip()
        name = simpledialog.askstring(
            "Enregistrer le profil",
            "Nom du profil :",
            initialvalue=current_name,
            parent=self.root,
        )
        if not name:
            return
        name = name.strip()
        if name in self._get_profiles() and not messagebox.askyesno(
            "Mettre à jour le profil",
            f"Le profil « {name} » existe déjà. Remplacer son ordre, ses alias et ses apparences ?",
            parent=self.root,
        ):
            return
        order_pseudos = [self._all_windows[hwnd].pseudo for hwnd in self._managed_order if hwnd in self._all_windows]
        saved_aliases = {pseudo: alias.strip() for pseudo, alias in self.aliases.items() if alias.strip()}
        pr = Profile(
            name=name,
            order=order_pseudos,
            aliases=saved_aliases,
            created_at="",
            updated_at="",
            visuals=sanitize_character_visuals(self.character_visuals),
            game_mode=self.game_mode,
        )
        self.desired_order_pseudos = list(order_pseudos)
        save_profile(self.dirs["profiles"], pr)
        self._log(f"Profil '{name}' enregistré")
        self._refresh_profile_combo()
        self.selected_profile.set(name)
        self._active_profile_name = name
        self.settings.last_profile = name
        save_settings(self.settings_path, self.settings)

    def load_profile_selected(self):
        name = self.selected_profile.get().strip()
        if not name:
            messagebox.showwarning("Charger profil", "Sélectionne un profil.")
            return
        try:
            pr = load_profile(self.dirs["profiles"], name)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger: {e}")
            return

        self._apply_loaded_profile(pr)
        self.apply_order_by_pseudo(pr.order)
        self._log(f"Profil '{name}' chargé")
        self.settings.last_profile = name
        save_settings(self.settings_path, self.settings)
        self.update_listboxes()

    def delete_profile_selected(self):
        name = self.selected_profile.get().strip()
        if not name:
            return
        if not messagebox.askyesno("Confirmer", f"Supprimer le profil '{name}' ?"):
            return
        try:
            delete_profile(self.dirs["profiles"], name)
            self._log(f"Profil '{name}' supprimé")
            if name == self._active_profile_name:
                self._active_profile_name = ""
            self.selected_profile.set("")
            self._refresh_profile_combo()
        except Exception as e:
            messagebox.showerror("Erreur", f"Suppression impossible: {e}")

    def export_profile_json(self):
        name = self.selected_profile.get().strip()
        if not name:
            messagebox.showwarning("Exporter", "Sélectionne un profil.")
            return
        try:
            pr = load_profile(self.dirs["profiles"], name)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger: {e}")
            return
        path = filedialog.asksaveasfilename(
            title="Exporter le profil",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile=f"{name}.json",
        )
        if not path:
            return
        atomic_write_text(Path(path), json_dump(pr.to_dict()))
        self._log(f"Profil exporté: {path}")

    def import_profile_json(self):
        path = filedialog.askopenfilename(title="Importer un profil", filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            data = json_load(Path(path))
            pr = Profile.from_dict(data)
            if not pr.name:
                pr.name = Path(path).stem
            save_profile(self.dirs["profiles"], pr)
            self._log(f"Profil importé: '{pr.name}'")
            self._refresh_profile_combo()
            self.selected_profile.set(pr.name)
        except Exception as e:
            messagebox.showerror("Erreur", f"Import impossible: {e}")

    def open_profile_manager(self) -> None:
        win = Toplevel(self.root)
        win.title("Gérer les profils")
        win.transient(self.root)
        win.grab_set()
        win.resizable(False, False)

        content = TtkFrame(win, padding=12)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)

        TtkLabel(content, text="Profil sélectionné").grid(row=0, column=0, columnspan=2, sticky="w")
        manager_combo = Combobox(
            content,
            textvariable=self.selected_profile,
            values=self._get_profiles(),
            state="readonly",
            width=36,
        )
        manager_combo.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(3, 10))

        TtkLabel(
            content,
            text=(
                "Enregistrer conserve le profil dans l’application. "
                "L’import et l’export JSON servent à transférer une copie vers un autre PC."
            ),
            style="Muted.TLabel",
            wraplength=380,
            justify="left",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 10))

        def refresh_values() -> None:
            values = self._get_profiles()
            self._refresh_profile_combo()
            manager_combo.configure(values=values)

        def import_profile() -> None:
            self.import_profile_json()
            refresh_values()

        def delete_selected_profile() -> None:
            self.delete_profile_selected()
            refresh_values()

        TtkButton(content, text="Importer un JSON…", command=import_profile).grid(
            row=3, column=0, sticky="ew", padx=(0, 3), pady=2
        )
        TtkButton(content, text="Exporter une copie…", command=self.export_profile_json).grid(
            row=3, column=1, sticky="ew", padx=(3, 0), pady=2
        )
        TtkButton(content, text="Supprimer le profil", command=delete_selected_profile).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=2
        )
        TtkButton(content, text="Fermer", command=win.destroy).grid(
            row=5, column=0, columnspan=2, sticky="e", pady=(10, 0)
        )

    def install_streamdeck_plugin(self) -> None:
        try:
            open_streamdeck_plugin()
        except FileNotFoundError as exc:
            messagebox.showerror(
                "Plugin Stream Deck introuvable",
                f"Le paquet d’installation n’est pas inclus dans cette copie de l’application.\n\n{exc}",
                parent=self.root,
            )
            return
        except OSError as exc:
            messagebox.showerror("Installation impossible", str(exc), parent=self.root)
            return
        except Exception as exc:
            messagebox.showerror(
                "Installation impossible",
                f"Impossible d’ouvrir le paquet Stream Deck : {exc}",
                parent=self.root,
            )
            return

        self._log("Installation ou mise à jour du plugin Stream Deck ouverte")

    def open_streamdeck_preview(self) -> None:
        existing = self.streamdeck_preview_window
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.deiconify()
                    existing.lift()
                    existing.focus_force()
                    return
            except Exception:
                pass

        win = Toplevel(self.root)
        self.streamdeck_preview_window = win
        self._streamdeck_preview_buttons = {}
        win.title("Aperçu Stream Deck — profil 15 touches")
        win.resizable(False, False)
        win.transient(self.root)

        content = TtkFrame(win, padding=14)
        content.pack(fill="both", expand=True)
        TtkLabel(content, text="Aperçu interactif du profil par défaut", style="Header.TLabel").pack(anchor="w")
        TtkLabel(
            content,
            text=(
                "Les huit touches centrales reprennent l’ordre actuel. Cliquez sur une touche pour tester son action ; "
                "les réglages visuels personnalisés restent gérés par Stream Deck."
            ),
            style="Muted.TLabel",
            wraplength=650,
            justify="left",
        ).pack(anchor="w", pady=(2, 12))

        deck = TtkFrame(content)
        deck.pack(fill="both", expand=True)
        for column in range(5):
            deck.columnconfigure(column, weight=1)

        action_commands = {
            "move-up": lambda: self._execute_preview_command("reorder", {"direction": "up"}),
            "move-down": lambda: self._execute_preview_command("reorder", {"direction": "down"}),
            "show": lambda: self._execute_preview_command("show", {}),
            "toggle-ignore": lambda: self._execute_preview_command("toggle_ignore", {}),
            "refresh": lambda: self._execute_preview_command("refresh", {}),
            "previous": lambda: self._execute_preview_command("rotate", {"direction": "backward"}),
            "next": lambda: self._execute_preview_command("rotate", {"direction": "forward"}),
        }

        for row_index, row in enumerate(STREAMDECK_PROFILE_LAYOUT):
            for column_index, key in enumerate(row):
                if isinstance(key, int):
                    button = TtkButton(
                        deck,
                        text=f"Case {key}\nPersonnage\nindisponible",
                        width=13,
                        style="StreamDeck.TButton",
                    )
                    button.state(["disabled"])
                    self._streamdeck_preview_buttons[key] = button
                else:
                    button = TtkButton(
                        deck,
                        text=STREAMDECK_ACTION_LABELS[key],
                        command=action_commands[key],
                        width=13,
                        style="StreamDeck.TButton",
                    )
                button.grid(row=row_index, column=column_index, sticky="nsew", padx=4, pady=4, ipady=7)

        TtkButton(content, text="Fermer", command=self._close_streamdeck_preview).pack(anchor="e", pady=(12, 0))
        win.protocol("WM_DELETE_WINDOW", self._close_streamdeck_preview)

        self._publish_streamdeck_state()
        self._poll_streamdeck_preview()

    def _close_streamdeck_preview(self) -> None:
        win = self.streamdeck_preview_window
        job = self._streamdeck_preview_poll_job
        self._streamdeck_preview_poll_job = None
        if win is not None and job is not None:
            try:
                win.after_cancel(job)
            except Exception:
                pass
        self.streamdeck_preview_window = None
        self._streamdeck_preview_buttons = {}
        if win is not None:
            try:
                win.destroy()
            except Exception:
                pass

    def _poll_streamdeck_preview(self) -> None:
        win = self.streamdeck_preview_window
        if win is None:
            return
        try:
            if not win.winfo_exists():
                return
            self._refresh_streamdeck_preview()
            self._streamdeck_preview_poll_job = win.after(750, self._poll_streamdeck_preview)
        except Exception:
            self._streamdeck_preview_poll_job = None

    def _refresh_streamdeck_preview(self) -> None:
        win = self.streamdeck_preview_window
        if win is None:
            return
        try:
            if not win.winfo_exists():
                return
        except Exception:
            return

        entries_by_slot = {
            int(entry["slot"]): entry
            for entry in self._streamdeck_preview_entries
            if isinstance(entry.get("slot"), int)
        }
        foreground_hwnd = get_foreground_hwnd()
        active_hwnd = foreground_hwnd if foreground_hwnd in self._all_windows else None
        if active_hwnd is None and self._managed_order:
            self.rotation_index %= len(self._managed_order)
            active_hwnd = self._managed_order[self.rotation_index]

        for slot, button in self._streamdeck_preview_buttons.items():
            entry = entries_by_slot.get(slot)
            if entry is None:
                button.configure(
                    text=f"Case {slot}\nPersonnage\nindisponible",
                    style="StreamDeck.TButton",
                    command=lambda: None,
                )
                button.state(["disabled"])
                continue

            hwnd = int(entry["hwnd"])
            ignored = bool(entry.get("ignored"))
            attention = bool(entry.get("attention"))
            style = (
                "StreamDeckAttention.TButton"
                if attention
                else "StreamDeckActive.TButton"
                if hwnd == active_hwnd
                else "StreamDeckIgnored.TButton"
                if ignored
                else "StreamDeck.TButton"
            )
            position = entry.get("position")
            button.configure(
                text=format_character_key(
                    int(position) if isinstance(position, int) else None,
                    str(entry.get("pseudo") or entry.get("name") or ""),
                    str(entry.get("character_class") or ""),
                    str(entry.get("alias") or ""),
                ),
                style=style,
                command=lambda target=hwnd: self._execute_preview_command("focus", {"hwnd": target}),
            )
            button.state(["!disabled"])

    def _execute_preview_command(self, command: str, payload: dict[str, object]) -> None:
        try:
            result = self._execute_streamdeck_command(command, payload)
        except Exception as exc:
            result = {"ok": False, "error": str(exc)}
        if not result.get("ok"):
            messagebox.showwarning(
                "Action Stream Deck impossible",
                str(result.get("error") or "La commande n’a pas pu être exécutée."),
                parent=self.streamdeck_preview_window or self.root,
            )
        self._refresh_streamdeck_preview()

    def _diagnostic_rows(self) -> list[tuple[str, object]]:
        bridge = self.streamdeck_bridge
        bridge_running = bool(bridge and bridge.is_running)
        installed_manifest = installed_plugin_manifest()
        installed_version = read_manifest_version(installed_manifest)
        bundled_package = Path(
            resource_path(
                "streamdeck-plugin",
                "com.remyducros.dofuswindowmanager.streamDeckPlugin",
            )
        )
        bundled_version = read_packaged_plugin_version(bundled_package)
        return [
            ("Version de l’application", __version__),
            ("Version de publication", __release_tag__),
            ("Mode de jeu", self.game_label),
            ("Thème", self.settings.theme),
            (
                "Notification après changement de fenêtre",
                (
                    f"active · {SWAP_POSITION_LABELS.get(self.settings.swap_notification_anchor, 'position inconnue')}"
                    if self.settings.swap_notification_enabled
                    else "désactivée"
                ),
            ),
            (
                "Overlay de rotation",
                (
                    f"actif · {self.settings.rotation_overlay_opacity}% · "
                    f"{'verrouillé' if self.settings.rotation_overlay_locked else 'déverrouillé'}"
                    if self.settings.rotation_overlay_enabled
                    else "désactivé"
                ),
            ),
            ("Profil actif", self.selected_profile.get().strip() or "aucun"),
            ("Fenêtres gérées", len(self._managed_order)),
            ("Fenêtres ignorées", len(self._ignored)),
            ("Fenêtres en attente d’attention", len(self.attention_state.snapshot())),
            ("Révision du scan", self._scan_revision),
            ("API locale Stream Deck", f"active sur le port {bridge.port}" if bridge_running else "inactive"),
            (
                "Dernière activité Stream Deck",
                format_activity(bridge.last_request_at if bridge else None),
            ),
            ("Plugin installé", installed_version or "non détecté"),
            ("Plugin fourni avec l’application", bundled_version or "indisponible"),
            ("WinEventHook", "actif" if self.win_events and self.win_events.is_running() else "inactif"),
            (
                "Détection du clignotement Windows",
                "active" if self.shell_attention and self.shell_attention.is_running() else "inactive",
            ),
            (
                "Privilèges incompatibles suspectés",
                "oui" if self._privilege_mismatch_suspected else "non",
            ),
            ("Démarrage Windows", "activé" if self.settings.start_with_windows else "désactivé"),
            (
                "Recherche automatique des mises à jour",
                "activée" if self.settings.check_updates_automatically else "désactivée",
            ),
            ("Dernière recherche de mise à jour", self.settings.last_update_check_at or "jamais"),
            ("Dossier des données", self.dirs["root"]),
            ("Dossier des journaux", self.dirs["logs"]),
        ]

    def open_diagnostics_window(self) -> None:
        win = Toplevel(self.root)
        win.title("Diagnostic")
        win.transient(self.root)
        win.resizable(False, False)

        content = TtkFrame(win, padding=12)
        content.pack(fill="both", expand=True)
        TtkLabel(content, text="État de Dofus Window Manager", style="Header.TLabel").pack(anchor="w")
        TtkLabel(
            content,
            text="Ce rapport peut être copié pour faciliter le dépannage.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(0, 8))

        report = build_diagnostic_report(self._diagnostic_rows())
        report_text = Text(content, width=78, height=20, wrap="word")
        report_text.insert("1.0", report)
        report_text.configure(state="disabled")
        report_text.pack(fill="both", expand=True)

        buttons = TtkFrame(content)
        buttons.pack(fill="x", pady=(10, 0))

        def copy_report() -> None:
            self.root.clipboard_clear()
            self.root.clipboard_append(report)
            self._log("Rapport de diagnostic copié")

        def open_logs() -> None:
            opener = getattr(os, "startfile", None)
            if callable(opener):
                opener(str(self.dirs["logs"]))
                return
            messagebox.showinfo("Journaux", str(self.dirs["logs"]), parent=win)

        TtkButton(buttons, text="Copier le rapport", command=copy_report).pack(side="left")
        TtkButton(buttons, text="Ouvrir les journaux", command=open_logs).pack(side="left", padx=(6, 0))
        TtkButton(buttons, text="Fermer", command=win.destroy).pack(side="right")

    def open_configuration_manager(self) -> None:
        win = Toplevel(self.root)
        win.title("Sauvegarde et restauration")
        win.transient(self.root)
        win.resizable(False, False)

        content = TtkFrame(win, padding=12)
        content.pack(fill="both", expand=True)
        TtkLabel(content, text="Configuration de l’application", style="Header.TLabel").pack(anchor="w")
        TtkLabel(
            content,
            text=(
                "La sauvegarde contient les réglages, profils, alias et l’ordre actuel. "
                "Les préférences internes du logiciel Stream Deck restent gérées par Stream Deck."
            ),
            style="Muted.TLabel",
            wraplength=460,
            justify="left",
        ).pack(anchor="w", pady=(0, 12))

        TtkButton(content, text="Exporter une sauvegarde complète…", command=self.export_configuration).pack(
            fill="x", pady=3
        )
        TtkButton(content, text="Importer une sauvegarde…", command=self.import_configuration).pack(
            fill="x", pady=3
        )
        TtkButton(content, text="Réinitialiser les réglages…", command=self.reset_settings).pack(
            fill="x", pady=3
        )
        TtkButton(content, text="Fermer", command=win.destroy).pack(anchor="e", pady=(12, 0))

    def export_configuration(self) -> None:
        profiles: list[Profile] = []
        for name in self._get_profiles():
            try:
                profiles.append(load_profile(self.dirs["profiles"], name))
            except Exception as exc:
                self._log(f"Profil ignoré pendant la sauvegarde ({name}) : {exc}")

        self.settings.auto_refresh = bool(self.auto_refresh_enabled.get())
        self.settings.last_profile = self.selected_profile.get().strip()
        current_order = [
            self._all_windows[hwnd].pseudo for hwnd in self._managed_order if hwnd in self._all_windows
        ]
        backup = build_configuration_backup(
            self.settings,
            profiles,
            active_profile=self.selected_profile.get(),
            current_order=current_order,
            current_aliases=self.aliases,
            app_version=__version__,
        )
        path = filedialog.asksaveasfilename(
            title="Exporter la configuration",
            defaultextension=".json",
            filetypes=[("Sauvegarde DWM", "*.json")],
            initialfile=f"DWM_sauvegarde_{datetime.now():%Y-%m-%d}.json",
        )
        if not path:
            return
        atomic_write_text(Path(path), json_dump(backup) + "\n")
        self._log(f"Configuration sauvegardée : {path}")

    def import_configuration(self) -> None:
        path = filedialog.askopenfilename(
            title="Importer une configuration",
            filetypes=[("Sauvegarde DWM", "*.json"), ("Tous les fichiers", "*.*")],
        )
        if not path:
            return
        try:
            restored_settings, profiles, session = parse_configuration_backup(json_load(Path(path)))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Sauvegarde invalide", str(exc), parent=self.root)
            return

        if not messagebox.askyesno(
            "Restaurer la configuration",
            (
                f"Importer {len(profiles)} profil(s) et remplacer les réglages actuels ?\n\n"
                "Les profils portant le même nom seront mis à jour. Les autres profils locaux seront conservés."
            ),
            parent=self.root,
        ):
            return

        try:
            set_startup_enabled(restored_settings.start_with_windows)
        except OSError as exc:
            restored_settings.start_with_windows = False
            messagebox.showwarning(
                "Démarrage Windows",
                f"Le démarrage automatique n’a pas pu être restauré : {exc}",
                parent=self.root,
            )

        for profile in profiles:
            save_profile(self.dirs["profiles"], profile)

        restored_settings.game_mode = restored_settings.game_mode or self.game_mode
        self.settings = restored_settings
        self._legacy_character_visuals = sanitize_character_visuals(
            self.settings.character_visuals
        )
        self.character_visuals = dict(self._legacy_character_visuals)
        set_language(self.settings.language)
        save_settings(self.settings_path, self.settings)
        self.auto_refresh_enabled.set(self.settings.auto_refresh)
        self._apply_window_column_order(list(self.settings.window_column_order or ()), persist=False)
        try:
            self._apply_runtime_theme(self.settings.theme)
        except Exception:
            self.settings.theme = MODERN_DARK_THEME
            self._apply_runtime_theme(self.settings.theme)
            save_settings(self.settings_path, self.settings)
        self._apply_display_preferences()
        self._localize_ui()
        self._refresh_profile_combo()

        active_profile = str(session.get("active_profile") or "")
        order = list(session.get("order") or [])
        aliases = dict(session.get("aliases") or {})
        self.selected_profile.set(active_profile)
        self._active_profile_name = active_profile
        if active_profile:
            try:
                active_profile_data = load_profile(self.dirs["profiles"], active_profile)
                if active_profile_data.visuals is not None:
                    self.character_visuals = sanitize_character_visuals(
                        active_profile_data.visuals
                    )
            except Exception:
                pass
        self.aliases.clear()
        self.aliases.update(aliases)
        self.desired_order_pseudos = order
        if order:
            self.apply_order_by_pseudo(order)
        self.update_listboxes()
        self._register_hotkeys()
        self._log(f"Configuration restaurée depuis {path}")
        messagebox.showinfo(
            "Configuration restaurée",
            "La configuration est restaurée. Redémarrez l’application pour appliquer complètement les options de détection.",
            parent=self.root,
        )

    def reset_display_settings(self, *, parent=None) -> bool:
        dialog_parent = parent or self.root
        if not messagebox.askyesno(
            "Réinitialiser l’affichage",
            (
                "Rétablir le thème, les colonnes, la notification et l’overlay par défaut ?\n\n"
                "Les profils, alias, portraits, icônes et raccourcis seront conservés."
            ),
            parent=dialog_parent,
        ):
            return False

        self.settings.reset_display_preferences(self.game_mode)
        save_settings(self.settings_path, self.settings)
        self._apply_window_column_order(list(self.settings.window_column_order or ()), persist=False)
        self._apply_runtime_theme(self.settings.theme)
        self._apply_display_preferences()
        self._attention_blink_phase = True
        self._apply_attention_blink_visuals()
        self._refresh_character_preview()
        self.update_listboxes()
        try:
            self.main_canvas.yview_moveto(0)
        except Exception:
            pass
        self._publish_streamdeck_state()
        self._log("Affichage réinitialisé")
        messagebox.showinfo(
            "Affichage réinitialisé",
            "L’affichage par défaut est restauré et l’overlay est activé à sa position initiale.",
            parent=dialog_parent,
        )
        return True

    def reset_settings(self) -> None:
        if not messagebox.askyesno(
            "Réinitialiser les réglages",
            "Revenir aux réglages par défaut ? Les profils et alias enregistrés ne seront pas supprimés.",
            parent=self.root,
        ):
            return
        try:
            set_startup_enabled(False)
        except OSError:
            pass
        self.settings = Settings(game_mode=self.game_mode)
        set_language(self.settings.language)
        save_settings(self.settings_path, self.settings)
        self.auto_refresh_enabled.set(self.settings.auto_refresh)
        self._apply_window_column_order(list(self.settings.window_column_order or ()), persist=False)
        self._apply_runtime_theme(self.settings.theme)
        self._apply_display_preferences()
        self._attention_blink_phase = True
        self._apply_attention_blink_visuals()
        self._localize_ui()
        self._refresh_character_preview()
        self.update_listboxes()
        try:
            self.main_canvas.yview_moveto(0)
        except Exception:
            pass
        self._publish_streamdeck_state()
        self._log("Réglages réinitialisés")
        messagebox.showinfo(
            "Réglages réinitialisés",
            "Les réglages par défaut seront entièrement appliqués au prochain démarrage.",
            parent=self.root,
        )

    # ---------------------------- Windows refresh ----------------------------

    def _on_game_mode_selected(self, _event=None) -> None:
        requested_mode = normalize_game_mode(self.game_mode_var.get(), self.game_mode)
        self.switch_game_mode(requested_mode)

    def switch_game_mode(self, game_mode: str) -> bool:
        """Switch Unity/Retro immediately without restarting the application."""
        new_mode = normalize_game_mode(game_mode, self.game_mode)
        if new_mode == self.game_mode:
            self.game_mode_var.set(self.game_label)
            return False

        previous_label = self.game_label
        self.settings.remember_display_preferences(self.game_mode)
        self._stop_win_event_hook()
        if self.popup_watcher is not None:
            self._shutdown_popup_watcher()

        self.game_mode = new_mode
        self.game_label = game_mode_label(new_mode)
        self.settings.game_mode = new_mode
        self.settings.activate_display_preferences(new_mode)
        selected_theme = (self.settings.theme_by_game_mode or {}).get(
            new_mode,
            default_theme_for_mode(new_mode),
        )
        self._apply_runtime_theme(selected_theme)
        self._apply_display_preferences()
        self._game_mode_revision += 1
        self.game_mode_var.set(self.game_label)
        self.game_subtitle_var.set(
            tr("Mode {game} · gestion locale des fenêtres", game=self.game_label)
        )
        self.root.title(f"Dofus Window Manager {__version__} ({self.game_label})")

        # Window handles, ignored state and Stream Deck slots belong to the
        # previous client generation. Profile aliases/order remain available
        # and will be reapplied to the newly detected characters.
        self._all_windows.clear()
        self._managed_order.clear()
        self._ignored.clear()
        self._streamdeck_order.clear()
        self.rotation_index = 0
        self._active_game_hwnd = None
        self.attention_state.reset()
        self._windows_sig = tuple()
        self.update_listboxes()
        self._publish_streamdeck_state()

        save_settings(self.settings_path, self.settings)
        self._start_win_event_hook()
        if self.game_mode == "retro" and self._popup_watch_enabled:
            self._set_popup_watch_enabled(True)

        self._log(f"Mode Dofus : {previous_label} → {self.game_label}")
        if self._refresh_inflight:
            self._refresh_again_requested = True
        else:
            self.refresh_windows(force=True)
        return True

    def _start_win_event_hook(self) -> None:
        if not getattr(self.settings, "event_hook_enabled", True):
            return
        self._stop_win_event_hook()
        try:
            classes, keyword_map = win_event_filter(self.game_mode, self.settings.retro_title_keyword)
            self.win_events = WinEventHook(
                lambda evt, hwnd: self._queue.put(("wevt", evt, hwnd)),
                class_names=classes,
                title_keyword_by_class=keyword_map,
            )
            self.win_events.start()
            error = self.win_events.get_last_error()
            if error:
                self._log(f"WinEventHook: {error}")
            self.shell_attention = ShellAttentionHook(
                lambda evt, hwnd: self._queue.put(("wevt", evt, hwnd))
            )
            self.shell_attention.start()
            shell_error = self.shell_attention.get_last_error()
            if shell_error:
                self._log(f"Attention Windows : repli Shell indisponible ({shell_error})")
        except Exception as exc:
            self._log(f"WinEventHook: impossible de démarrer ({exc})")
            self.win_events = None

    def _stop_win_event_hook(self) -> None:
        hook = getattr(self, "win_events", None)
        if hook is not None:
            try:
                hook.stop()
            except Exception:
                pass
        self.win_events = None
        shell_hook = getattr(self, "shell_attention", None)
        if shell_hook is not None:
            try:
                shell_hook.stop()
            except Exception:
                pass
        self.shell_attention = None

    def refresh_windows(self, quiet: bool = False, force: bool = False) -> bool:
        """Scan game windows in a background thread.

        - quiet=True avoids extra logs (useful for auto-refresh).
        - force=True bypasses debounce.
        """
        if self._refresh_inflight:
            if force:
                self._refresh_again_requested = True
            return False

        now = time.monotonic()
        if (not force) and quiet:
            if (now - self._last_scan_monotonic) < self._min_scan_interval_sec:
                return False

        self._last_scan_monotonic = now
        self._refresh_inflight = True
        mode_revision = self._game_mode_revision
        scan_mode = self.game_mode
        game_label = self.game_label
        if not quiet:
            self._log(f"Scan des fenêtres {game_label}...")

        def worker():
            try:
                wins = list_game_windows(scan_mode, self.settings.retro_title_keyword, self.settings.retro_process_keyword)
                enum_error = get_last_enum_error()
                if not wins and enum_error:
                    self._queue.put(("error", mode_revision, f"Erreur scan Win32: {enum_error}"))
                else:
                    self._queue.put(("windows", mode_revision, wins))
                    if not wins:
                        candidates = list_visible_dofus_candidates()
                        if candidates:
                            sample = "; ".join(
                                f"{title} [classe={class_name or 'inconnue'}]"
                                for _hwnd, title, class_name in candidates[:4]
                            )
                            self._queue.put(
                                (
                                    "notice",
                                    mode_revision,
                                    "Fenêtre(s) Dofus visible(s), mais non reconnue(s) par le mode "
                                    f"{game_label}: {sample}",
                                )
                            )
            except Exception as e:
                self._queue.put(("error", mode_revision, f"Erreur scan: {e}"))

        threading.Thread(target=worker, daemon=True).start()
        return True

    def _finish_refresh(self) -> None:
        """Publish scan completion and run one explicitly queued refresh."""
        self._refresh_inflight = False
        self._scan_revision += 1
        self._publish_streamdeck_state()
        if self._refresh_again_requested:
            self._refresh_again_requested = False
            self.root.after(0, lambda: self.refresh_windows(quiet=True, force=True))

    def _apply_windows(self, wins: list[GameWindow]):
        # Update map
        new_map = {w.hwnd: w for w in wins}
        self._all_windows = new_map
        self.attention_state.discard_unknown(new_map.keys())
        if self._active_game_hwnd not in new_map:
            self._active_game_hwnd = None

        # Compute a lightweight signature to detect whether the scan changed.
        new_sig = tuple(sorted((w.hwnd, w.title) for w in wins))
        unchanged = new_sig == self._windows_sig
        self._windows_sig = new_sig

        # If nothing changed, just update the timestamp and skip rebuilding the UI.
        if unchanged:
            self.last_update_time.set(datetime.now().strftime("Dernier scan: %H:%M:%S"))
            return

        # Heuristic: detect privilege mismatch (Dofus launched as admin but this tool isn't).
        # This can make focus/hotkeys feel "random" on some setups.
        try:
            suspected = suspect_privilege_mismatch(list(new_map.keys()))
        except Exception:
            suspected = False
        if suspected and not self._privilege_mismatch_suspected:
            self._log(
                "Avertissement: possible différence de privilèges (admin/non-admin). "
                "Lance le manager au même niveau que Dofus si le focus ou les hotkeys semblent capricieux."
            )
        self._privilege_mismatch_suspected = bool(suspected)

        # Remove disappeared
        self._ignored = {hwnd for hwnd in self._ignored if hwnd in new_map}
        self._managed_order = [hwnd for hwnd in self._managed_order if hwnd in new_map and hwnd not in self._ignored]

        # Add new ones at end (managed)
        for hwnd in new_map.keys():
            if hwnd not in self._ignored and hwnd not in self._managed_order:
                self._managed_order.append(hwnd)

        # Apply current profile order (if loaded)
        if self.desired_order_pseudos:
            self.apply_order_by_pseudo(self.desired_order_pseudos)

        self._streamdeck_order = reconcile_streamdeck_order(
            self._streamdeck_order,
            self._all_windows,
            (*self._managed_order, *sorted(self._ignored)),
        )

        # Reset rotation index if out-of-range
        if self._managed_order:
            self.rotation_index %= len(self._managed_order)
        else:
            self.rotation_index = 0

        self.last_update_time.set(datetime.now().strftime("Dernier scan: %H:%M:%S"))
        self._log(f"{len(self._managed_order)} gérées, {len(self._ignored)} ignorées")
        self.update_listboxes()
        self._update_popup_watcher_targets()

    def _schedule_refresh(self):
        if self._stop_event.is_set():
            return
        if self.auto_refresh_enabled.get():
            self.refresh_windows(quiet=True)
        self.root.after(max(2, int(self.settings.refresh_seconds)) * 1000, self._schedule_refresh)

    def _on_toggle_autorefresh(self):
        self.settings.auto_refresh = bool(self.auto_refresh_enabled.get())
        save_settings(self.settings_path, self.settings)

    def _process_queue(self):
        while True:
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                break

            kind = item[0]
            if kind == "windows":
                if int(item[1]) == self._game_mode_revision:
                    self._apply_windows(item[2])
                self._finish_refresh()
            elif kind == "error":
                if int(item[1]) == self._game_mode_revision:
                    self._log(str(item[2]))
                self._finish_refresh()
            elif kind == "notice":
                if int(item[1]) == self._game_mode_revision:
                    self._log(str(item[2]))
            elif kind == "streamdeck":
                response_queue = item[3]
                try:
                    result = self._execute_streamdeck_command(str(item[1]), item[2])
                except Exception as exc:
                    result = {"ok": False, "error": str(exc), "_status": 503}
                try:
                    response_queue.put_nowait(result)
                except queue.Full:
                    pass
            elif kind == "wevt":
                # Window event hook notifications (create/destroy/namechange)
                try:
                    _evt, _hwnd = item[1], int(item[2])
                    self._apply_win_event(str(_evt), _hwnd)
                except Exception:
                    pass
            elif kind == "tray":
                action = str(item[1])
                if action == "show":
                    self._show_main_window()
                elif action == "refresh":
                    self.refresh_windows(force=True)
                elif action == "quit":
                    self.on_close(force=True)
            elif kind == "update_check":
                self._finish_update_check(
                    manual=bool(item[1]),
                    result=item[2] if isinstance(item[2], UpdateCheckResult) else None,
                    error=str(item[3] or ""),
                    checked_at=str(item[4] or ""),
                )

            self._queue.task_done()
            if self._stop_event.is_set():
                return

        if not self._stop_event.is_set():
            self.root.after(100, self._process_queue)

    # ---------------------------- Stream Deck bridge ----------------------------

    def _dispatch_streamdeck_command(self, command: str, payload: dict[str, object]) -> dict[str, object]:
        """Queue a bridge command so every Tk/Win32 mutation stays on the UI thread."""
        if self._stop_event.is_set():
            return {"ok": False, "error": "L'application est en cours de fermeture.", "_status": 503}

        response_queue: "queue.Queue[dict[str, object]]" = queue.Queue(maxsize=1)
        self._queue.put(("streamdeck", command, payload, response_queue))
        try:
            return response_queue.get(timeout=2.0)
        except queue.Empty as exc:
            raise TimeoutError("Délai de réponse de l'interface dépassé.") from exc

    def _execute_streamdeck_command(self, command: str, payload: dict[str, object]) -> dict[str, object]:
        if command == "show":
            self._show_main_window()
            return {"ok": True}

        if command == "refresh":
            revision_before = self._scan_revision
            was_inflight = self._refresh_inflight
            started = self.refresh_windows(quiet=True, force=True)
            target_revision = revision_before + (2 if was_inflight else 1)
            return {
                "ok": True,
                "accepted": started or self._refresh_again_requested,
                "target_revision": target_revision,
            }

        if command == "toggle_ignore":
            return self._toggle_ignore_current_window()

        if command == "reorder":
            direction = str(payload.get("direction", "")).strip().lower()
            if direction not in {"up", "down"}:
                return {"ok": False, "error": "Direction invalide.", "_status": 400}
            return self._reorder_current_window(direction)

        if command == "next_attention":
            return self._activate_next_attention(source="Stream Deck")

        if command == "rotate":
            direction = str(payload.get("direction", "")).strip().lower()
            if direction not in {"forward", "backward"}:
                return {"ok": False, "error": "Direction invalide.", "_status": 400}
            if not self.request_rotation(direction):
                return {"ok": False, "error": "Aucune fenêtre ne peut être activée.", "_status": 409}
            return {"ok": True, "accepted": True, "direction": direction}

        if command == "focus":
            raw_hwnd = payload.get("hwnd")
            slot: int | None = None
            if raw_hwnd is not None:
                if isinstance(raw_hwnd, bool):
                    return {"ok": False, "error": "Identifiant de fenêtre invalide.", "_status": 400}
                try:
                    hwnd = int(raw_hwnd)
                except (TypeError, ValueError):
                    return {"ok": False, "error": "Identifiant de fenêtre invalide.", "_status": 400}
                if hwnd not in self._all_windows:
                    return {"ok": False, "error": "Le personnage attribué n'est plus disponible.", "_status": 410}
                if hwnd in self._streamdeck_order:
                    slot = self._streamdeck_order.index(hwnd) + 1
            else:
                raw_slot = payload.get("slot")
                if isinstance(raw_slot, bool):
                    return {"ok": False, "error": "Numéro de case invalide.", "_status": 400}
                try:
                    slot = int(raw_slot)
                except (TypeError, ValueError):
                    return {"ok": False, "error": "Numéro de case invalide.", "_status": 400}

                if slot < 1 or slot > len(self._streamdeck_order):
                    return {"ok": False, "error": f"La case {slot} n'est pas attribuée.", "_status": 404}
                hwnd = self._streamdeck_order[slot - 1]

            window = self._all_windows.get(hwnd)
            if window is None or not is_window(hwnd):
                self.refresh_windows(quiet=True, force=True)
                return {"ok": False, "error": "La fenêtre n'existe plus.", "_status": 410}

            try:
                focus_hwnd(hwnd)
            except FocusError as exc:
                self._log(f"Stream Deck, focus échoué : {exc}")
                return {"ok": False, "error": str(exc), "_status": 409}

            self._record_character_focus(hwnd, notify=True)
            self._log(f"Stream Deck → {window.title}")
            return {
                "ok": True,
                "slot": slot,
                "hwnd": hwnd,
                "name": self.aliases.get(window.pseudo) or window.pseudo,
                "ignored": hwnd in self._ignored,
            }

        return {"ok": False, "error": "Commande inconnue.", "_status": 404}

    def _show_main_window(self) -> None:
        """Restore and foreground the manager when requested from Stream Deck."""
        overlay_ui = getattr(self, "overlay_ui", None)
        if overlay_ui is not None and overlay_ui.compact_is_open:
            overlay_ui.close_compact(show_root=False)
        try:
            self.root.deiconify()
            self.root.state("normal")
        except Exception:
            pass
        try:
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.after(180, lambda: self.root.attributes("-topmost", False))
            self.root.focus_force()
        except Exception:
            pass

    def _hide_main_window(self) -> None:
        if not self.tray.is_running:
            return
        try:
            self.root.withdraw()
        except Exception:
            return
        if not self._tray_notice_shown:
            self.tray.notify(
                "L’application continue de gérer les fenêtres et le Stream Deck. "
                "Utilisez l’icône de notification pour la rouvrir ou la quitter."
            )
            self._tray_notice_shown = True

    def _reorder_current_window(self, direction: str) -> dict[str, object]:
        foreground_hwnd = get_foreground_hwnd()
        if foreground_hwnd in self._ignored:
            return {
                "ok": False,
                "error": "La fenêtre actuelle est ignorée ; réintègre-la avant de modifier son ordre.",
                "_status": 409,
            }
        if foreground_hwnd in self._managed_order:
            hwnd = foreground_hwnd
        elif self._managed_order:
            self.rotation_index %= len(self._managed_order)
            hwnd = self._managed_order[self.rotation_index]
        else:
            return {"ok": False, "error": "Aucune fenêtre Dofus gérée.", "_status": 404}

        delta = -1 if direction == "up" else 1
        new_order = move_window_by_delta(self._managed_order, hwnd, delta)
        if new_order == self._managed_order:
            boundary = "première" if direction == "up" else "dernière"
            return {
                "ok": False,
                "error": f"Le personnage est déjà en {boundary} position.",
                "_status": 409,
            }

        self._managed_order = new_order
        self.rotation_index = self._managed_order.index(hwnd)
        self._publish_order_consumers()
        self.update_listboxes(publish_consumers=False)
        self._update_popup_watcher_targets()

        window = self._all_windows.get(hwnd)
        name = (self.aliases.get(window.pseudo) or window.pseudo) if window else str(hwnd)
        position = self.rotation_index + 1
        self._log(f"Stream Deck : {name} déplacé en position {position}")
        return {
            "ok": True,
            "direction": direction,
            "hwnd": hwnd,
            "name": name,
            "position": position,
        }

    def _publish_streamdeck_state(self) -> None:
        self._streamdeck_order = reconcile_streamdeck_order(
            self._streamdeck_order,
            self._all_windows,
            (*self._managed_order, *sorted(self._ignored)),
        )

        foreground_hwnd = get_foreground_hwnd()
        active_hwnd = foreground_hwnd if foreground_hwnd in self._all_windows else None
        if active_hwnd is None and self._managed_order:
            self.rotation_index %= len(self._managed_order)
            active_hwnd = self._managed_order[self.rotation_index]

        windows = build_streamdeck_windows(
            self._all_windows,
            self._streamdeck_order,
            self._managed_order,
            self._ignored,
            self.aliases,
            active_hwnd,
            self.attention_state.queue(),
            self._active_character_visuals(),
        )
        self._streamdeck_preview_entries = windows

        bridge = self.streamdeck_bridge
        if bridge is not None:
            bridge.update_snapshot(
                {
                    "api_version": 1,
                    "app_version": __version__,
                    "game_mode": self.game_mode,
                    "theme": self.settings.theme,
                    "language": self.settings.language,
                    "scan_revision": self._scan_revision,
                    "show_character_portraits": bool(self.settings.show_character_portraits),
                    "show_character_badges": bool(self.settings.show_character_badges),
                    "attention_blink_enabled": bool(self.settings.attention_blink_enabled),
                    "attention_blink_phase": bool(self._attention_blink_phase),
                    "attention_count": len(self.attention_state.queue()),
                    "next_attention_hwnd": self.attention_state.next(),
                    "windows": windows,
                }
            )
        self._refresh_streamdeck_preview()

    def _toggle_ignore_current_window(self) -> dict[str, object]:
        foreground_hwnd = get_foreground_hwnd()
        if foreground_hwnd in self._all_windows:
            hwnd = foreground_hwnd
        elif self._managed_order:
            self.rotation_index %= len(self._managed_order)
            hwnd = self._managed_order[self.rotation_index]
        else:
            return {"ok": False, "error": "Aucune fenêtre Dofus actuelle.", "_status": 404}

        window = self._all_windows.get(hwnd)
        if window is None:
            return {"ok": False, "error": "La fenêtre Dofus n'existe plus.", "_status": 410}

        if hwnd in self._ignored:
            self._ignored.remove(hwnd)
            if hwnd not in self._managed_order:
                self._managed_order.append(hwnd)
            self.rotation_index = self._managed_order.index(hwnd)
            ignored = False
            self._log(f"Stream Deck : fenêtre ré-ajoutée — {window.title}")
        else:
            if hwnd not in self._managed_order:
                return {"ok": False, "error": "La fenêtre actuelle n'est pas gérée.", "_status": 409}
            removed_index = self._managed_order.index(hwnd)
            self._managed_order.remove(hwnd)
            self._ignored.add(hwnd)
            if self._managed_order:
                if removed_index < self.rotation_index:
                    self.rotation_index -= 1
                self.rotation_index %= len(self._managed_order)
            else:
                self.rotation_index = 0
            ignored = True
            self._log(f"Stream Deck : fenêtre ignorée — {window.title}")

        self._sync_streamdeck_order_with_managed()
        self.update_listboxes()
        self._update_popup_watcher_targets()
        return {
            "ok": True,
            "ignored": ignored,
            "hwnd": hwnd,
            "name": window.pseudo,
        }

    # ---------------------------- WinEventHook sync ----------------------------

    def _request_ui_update(self):
        """Debounce UI rebuilds (listboxes) when many events arrive quickly."""
        if self._ui_update_pending:
            return
        self._ui_update_pending = True
        self.root.after(120, self._do_ui_update)

    def _do_ui_update(self):
        self._ui_update_pending = False
        self.last_update_time.set(datetime.now().strftime("Maj: %H:%M:%S"))
        self.update_listboxes()
        self._update_popup_watcher_targets()

    def _apply_win_event(self, evt: str, hwnd: int):
        """Apply a single window event (create/destroy/namechange) incrementally.

        This avoids full scans: we only query the single hwnd's class/title.
        """
        if self._stop_event.is_set():
            return

        evt = (evt or "").strip().lower()
        if not hwnd:
            return

        changed_structure = False  # add/remove/reorder -> needs UI update

        if evt == "destroy":
            if hwnd in self._all_windows:
                self._all_windows.pop(hwnd, None)
                self.attention_state.clear(hwnd)
                if hwnd == self._active_game_hwnd:
                    self._active_game_hwnd = None
                if hwnd in self._streamdeck_order:
                    self._streamdeck_order.remove(hwnd)
                if hwnd in self._ignored:
                    self._ignored.discard(hwnd)
                if hwnd in self._managed_order:
                    try:
                        self._managed_order.remove(hwnd)
                    except ValueError:
                        pass
                changed_structure = True

        elif evt == "attention":
            foreground_hwnd = get_foreground_hwnd()
            active_target = hwnd if foreground_hwnd == hwnd else None
            if self.attention_state.mark(hwnd, self._all_windows.keys(), active_target):
                window = self._all_windows.get(hwnd)
                self._log(
                    f"Attention demandée : {window.pseudo if window else hwnd}"
                )
                self.update_listboxes()
            return

        elif evt == "foreground":
            if hwnd not in self._all_windows:
                return
            self._record_character_focus(hwnd, notify=False)
            return

        elif evt in ("create", "namechange"):
            # Validate window still exists
            try:
                if not is_window(hwnd):
                    return
            except Exception:
                return

            cn = get_class_name(hwnd)
            title = get_window_title(hwnd)
            if not title:
                return

            if self.game_mode == "unity":
                if cn != "UnityWndClass":
                    return
                pseudo = extract_pseudo_unity(title)
                gw = GameWindow(
                    hwnd=hwnd,
                    title=title,
                    pseudo=pseudo,
                    character_class=extract_character_class(title, pseudo),
                )
            else:
                if cn != "Chrome_WidgetWin_1":
                    return
                kw = (self.settings.retro_title_keyword or "dofus retro v").lower().strip()
                if kw and kw not in title.lower():
                    return
                pseudo = extract_pseudo_retro(title)
                gw = GameWindow(
                    hwnd=hwnd,
                    title=title,
                    pseudo=pseudo,
                    character_class=extract_character_class(title, pseudo),
                )

            prev = self._all_windows.get(hwnd)
            if prev is None:
                self._all_windows[hwnd] = gw
                if hwnd not in self._streamdeck_order:
                    self._streamdeck_order.append(hwnd)
                if hwnd not in self._ignored and hwnd not in self._managed_order:
                    self._managed_order.append(hwnd)
                changed_structure = True
            elif prev.title != gw.title or prev.pseudo != gw.pseudo or prev.character_class != gw.character_class:
                # A title change also requires updating an optional capture target.
                self._all_windows[hwnd] = gw
                changed_structure = True

        else:
            return

        if not changed_structure:
            return

        # Keep rotation index valid
        if self._managed_order:
            self.rotation_index %= len(self._managed_order)
        else:
            self.rotation_index = 0

        # Update scan signature (cheap enough at event rate)
        try:
            self._windows_sig = tuple(sorted((w.hwnd, w.title) for w in self._all_windows.values()))
        except Exception:
            pass

        self._request_ui_update()

    # ---------------------------- List operations ----------------------------

    def _managed_hwnds_filtered(self) -> list[int]:
        q = self.search_var.get().strip().lower()
        if not q:
            return list(self._managed_order)
        out = []
        for hwnd in self._managed_order:
            w = self._all_windows.get(hwnd)
            if not w:
                continue
            alias = self.aliases.get(w.pseudo, "")
            if (
                q in w.title.lower()
                or q in w.pseudo.lower()
                or q in (w.character_class or "").lower()
                or (alias and q in alias.lower())
            ):
                out.append(hwnd)
        return out

    def _refresh_focus_views(self) -> None:
        """Update focus styling and consumers without rebuilding either table."""
        attention_hwnds = self.attention_state.snapshot()
        active_hwnd = self._active_game_hwnd
        for tree, show_active in (
            (self.managed_tree, True),
            (self.ignored_tree, False),
        ):
            for item in tree.get_children():
                try:
                    hwnd = int(item)
                except (TypeError, ValueError):
                    continue
                tags = tuple(
                    tag
                    for tag in tree.item(item, "tags")
                    if tag not in {"active", "attention"}
                )
                if hwnd in attention_hwnds:
                    tags += ("attention",)
                elif show_active and hwnd == active_hwnd:
                    tags += ("active",)
                tree.item(item, tags=tags)

        self._refresh_auxiliary_displays()
        self._publish_streamdeck_state()

    def update_listboxes(self, *, publish_consumers: bool = True):
        selected_managed = set(self.managed_tree.selection())
        selected_ignored = set(self.ignored_tree.selection())
        managed_items = self.managed_tree.get_children()
        ignored_items = self.ignored_tree.get_children()
        if managed_items:
            self.managed_tree.delete(*managed_items)
        if ignored_items:
            self.ignored_tree.delete(*ignored_items)

        filtered = self._managed_hwnds_filtered()
        attention_hwnds = self.attention_state.snapshot()
        active_hwnd = self._active_game_hwnd if self._active_game_hwnd in self._managed_order else None
        if active_hwnd is None and self._active_game_hwnd not in self._ignored and self._managed_order:
            self.rotation_index %= len(self._managed_order)
            active_hwnd = self._managed_order[self.rotation_index]

        for hwnd in filtered:
            w = self._all_windows.get(hwnd)
            if not w:
                continue
            alias = self.aliases.get(w.pseudo, "")
            tags = (
                ("attention",)
                if hwnd in attention_hwnds
                else ("active",)
                if hwnd == active_hwnd
                else ()
            )
            self.managed_tree.insert(
                "",
                "end",
                iid=str(hwnd),
                values=window_table_values(w, alias),
                tags=tags,
            )

        if not filtered:
            empty_text = tr("Aucune fenêtre détectée") if not self._all_windows else tr("Aucun résultat")
            self.managed_tree.insert(
                "",
                "end",
                iid="__empty_managed__",
                values=("", empty_text, "", ""),
                tags=("empty",),
            )

        ignored_order = [hwnd for hwnd in self._streamdeck_order if hwnd in self._ignored]
        ignored_order.extend(hwnd for hwnd in sorted(self._ignored) if hwnd not in ignored_order)
        for hwnd in ignored_order:
            w = self._all_windows.get(hwnd)
            if not w:
                continue
            self.ignored_tree.insert(
                "",
                "end",
                iid=str(hwnd),
                values=window_table_values(w, self.aliases.get(w.pseudo, "")),
                tags=(("attention",) if hwnd in attention_hwnds else ()),
            )

        if not ignored_order:
            self.ignored_tree.insert(
                "",
                "end",
                iid="__empty_ignored__",
                values=("", tr("Aucune fenêtre ignorée"), "", ""),
                tags=("empty",),
            )

        managed_children = set(self.managed_tree.get_children())
        managed_selection = next((item for item in selected_managed if item in managed_children), None)
        if managed_selection is None and active_hwnd is not None and str(active_hwnd) in managed_children:
            managed_selection = str(active_hwnd)
        if managed_selection:
            self.managed_tree.selection_set(managed_selection)
            self.managed_tree.see(managed_selection)

        ignored_children = set(self.ignored_tree.get_children())
        ignored_selection = next((item for item in selected_ignored if item in ignored_children), None)
        if ignored_selection:
            self.ignored_tree.selection_set(ignored_selection)
            self.ignored_tree.see(ignored_selection)

        if publish_consumers:
            self._publish_order_consumers()
        self._refresh_character_preview()
        self._update_next_attention_controls()

    def _selected_managed_hwnd(self) -> int | None:
        selection = self.managed_tree.selection()
        if not selection:
            return None
        try:
            return int(selection[0])
        except ValueError:
            return None

    def _selected_ignored_hwnd(self) -> int | None:
        selection = self.ignored_tree.selection()
        if not selection:
            return None
        try:
            return int(selection[0])
        except ValueError:
            return None

    def request_rotation(self, direction: str) -> bool:
        """Coalesce rapid UI/hotkey presses and focus only the final target."""
        if direction not in {"forward", "backward"} or not self._managed_order:
            return False
        self._pending_rotation_delta += 1 if direction == "forward" else -1
        if self._rotation_request_job is None:
            self._rotation_request_job = self.root.after(
                ROTATION_COALESCE_MS,
                self._flush_rotation_requests,
            )
        return True

    def _flush_rotation_requests(self) -> None:
        delta = self._pending_rotation_delta
        self._pending_rotation_delta = 0
        self._rotation_request_job = None
        if delta:
            self._rotate_by_delta(delta)

    def rotate(self, direction: str) -> bool:
        if direction not in {"forward", "backward"}:
            return False
        return self._rotate_by_delta(1 if direction == "forward" else -1)

    def _rotate_by_delta(self, delta: int) -> bool:
        if not self._managed_order or not delta:
            return False

        previous_hwnd = self._managed_order[self.rotation_index % len(self._managed_order)]
        step = 1 if delta > 0 else -1
        self.rotation_index = (self.rotation_index + int(delta)) % len(self._managed_order)
        attempts = 0
        focused = False
        structure_changed = False

        while self._managed_order and attempts < max(1, len(self._managed_order) + 1):
            hwnd = self._managed_order[self.rotation_index]
            window = self._all_windows.get(hwnd)

            # Window may have disappeared between scans; prune and try the next one.
            if (not window) or (not is_window(hwnd)):
                self._log("Fenêtre fermée détectée, mise à jour de la liste…")
                self._managed_order.remove(hwnd)
                self._ignored.discard(hwnd)
                structure_changed = True
                if not self._managed_order:
                    self.rotation_index = 0
                    self.update_listboxes()
                    self.refresh_windows()
                    return False
                if step < 0:
                    self.rotation_index -= 1
                self.rotation_index %= len(self._managed_order)
                attempts += 1
                continue

            try:
                focus_hwnd(hwnd)
                self._record_character_focus(hwnd, notify=True)
                self._log(f"Focus → {window.title}")
                focused = True
            except FocusError as exc:
                if previous_hwnd in self._managed_order:
                    self.rotation_index = self._managed_order.index(previous_hwnd)
                msg = f"Focus échoué: {exc}"
                if self._privilege_mismatch_suspected and "bloqu" in str(exc).lower():
                    msg += " (Astuce: lance le manager au même niveau de privilèges que Dofus.)"
                self._log(msg)
            break

        if structure_changed:
            self.update_listboxes()
        return focused

    def ignore_selected(self):
        hwnd = self._selected_managed_hwnd()
        if hwnd is None:
            # fallback: ignore current rotation
            if not self._managed_order:
                return
            hwnd = self._managed_order[self.rotation_index]

        if hwnd in self._managed_order:
            self._managed_order.remove(hwnd)
        self._ignored.add(hwnd)

        if self._managed_order:
            self.rotation_index %= len(self._managed_order)
        else:
            self.rotation_index = 0

        self._sync_streamdeck_order_with_managed()
        self._log("Fenêtre ignorée")
        self.update_listboxes()
        self._update_popup_watcher_targets()

    def unignore_selected(self):
        hwnd = self._selected_ignored_hwnd()
        if hwnd is None:
            return
        if hwnd in self._ignored:
            self._ignored.remove(hwnd)
        if hwnd not in self._managed_order and hwnd in self._all_windows:
            self._managed_order.append(hwnd)
        self._sync_streamdeck_order_with_managed()
        self._log("Fenêtre ré-ajoutée")
        self.update_listboxes()
        self._update_popup_watcher_targets()

    def move_selected(self, delta: int):
        hwnd = self._selected_managed_hwnd()
        if hwnd is None:
            return
        try:
            idx = self._managed_order.index(hwnd)
        except ValueError:
            return
        new_idx = idx + delta
        if not (0 <= new_idx < len(self._managed_order)):
            return
        self._managed_order.pop(idx)
        self._managed_order.insert(new_idx, hwnd)

        # keep rotation index consistent
        if self.rotation_index == idx:
            self.rotation_index = new_idx
        elif idx < self.rotation_index <= new_idx:
            self.rotation_index -= 1
        elif new_idx <= self.rotation_index < idx:
            self.rotation_index += 1

        self._publish_order_consumers()
        self.update_listboxes(publish_consumers=False)

    def _move_managed_window(self, hwnd: int, target_hwnd: int, *, after: bool) -> None:
        if hwnd not in self._managed_order or target_hwnd not in self._managed_order:
            return
        active_hwnd = self._managed_order[self.rotation_index] if self._managed_order else None
        new_order = move_window(self._managed_order, hwnd, target_hwnd, after=after)
        if new_order == self._managed_order:
            self.update_listboxes()
            return

        self._managed_order = new_order
        if active_hwnd in self._managed_order:
            self.rotation_index = self._managed_order.index(active_hwnd)
        self._publish_order_consumers()
        self.update_listboxes(publish_consumers=False)
        item = str(hwnd)
        if item in self.managed_tree.get_children():
            self.managed_tree.selection_set(item)
            self.managed_tree.see(item)
        self._log("Ordre des personnages modifié")

    def _sync_streamdeck_order_with_managed(self) -> None:
        self._streamdeck_order = align_streamdeck_slots_with_managed(
            self._streamdeck_order,
            self._managed_order,
            self._ignored,
        )

    def _publish_order_consumers(self) -> None:
        """Publish one managed-order snapshot to the overlay and Stream Deck."""
        self._sync_streamdeck_order_with_managed()
        self._refresh_auxiliary_displays()
        self._publish_streamdeck_state()

    def _on_character_tree_selected(self, tree: Treeview) -> None:
        selection = tree.selection()
        if selection:
            try:
                self._preview_selected_hwnd = int(selection[0])
            except ValueError:
                self._preview_selected_hwnd = None
        self._refresh_character_preview()

    def _selected_character_hwnd(self) -> int | None:
        if self._preview_selected_hwnd in self._all_windows:
            return self._preview_selected_hwnd
        return self._selected_managed_hwnd() or self._selected_ignored_hwnd()

    def _refresh_character_preview(self) -> None:
        label = getattr(self, "character_preview_image", None)
        if label is None:
            return
        hwnd = self._selected_character_hwnd()
        window = self._all_windows.get(hwnd) if hwnd is not None else None
        if window is None:
            self._character_preview_photo = None
            label.configure(image="", background=resolved_theme_palette(self.root, self.settings.theme)["bg2"])
            self.character_preview_var.set("Sélectionnez un personnage")
            return

        appearance = self._active_character_visuals().get(window.pseudo, {})
        palette = resolved_theme_palette(self.root, self.settings.theme)
        avatar = build_avatar_image(
            window.pseudo,
            portrait_data=str(appearance.get("portrait") or ""),
            badge=str(appearance.get("badge") or "none"),
            size=64,
            background=palette["bg3"],
            foreground=palette["on_dark"],
            show_badge=True,
        )
        photo = ImageTk.PhotoImage(avatar, master=self.root)
        self._character_preview_photo = photo
        label.configure(image=photo, background=palette["bg2"])
        alias = (self.aliases.get(window.pseudo) or "").strip() or "—"
        badge = badge_label(appearance.get("badge"))
        attention_order = self.attention_state.rank(hwnd)
        attention = (
            f"\n!{attention_order} Demande d’attention"
            if attention_order is not None
            else ""
        )
        self.character_preview_var.set(
            f"{window.pseudo}\n{window.character_class or 'Classe inconnue'}\n"
            f"Alias : {alias}\nIcône : {badge}{attention}"
        )

    def open_character_customization(self) -> None:
        hwnd = self._selected_character_hwnd()
        window = self._all_windows.get(hwnd) if hwnd is not None else None
        if window is None:
            messagebox.showwarning(
                "Personnaliser le personnage",
                "Sélectionnez d’abord une fenêtre Dofus.",
                parent=self.root,
            )
            return

        appearance = dict(self._active_character_visuals().get(window.pseudo, {}))
        portrait_data = str(appearance.get("portrait") or "")
        alias_var = StringVar(value=self.aliases.get(window.pseudo, ""))
        badge_var = StringVar(value=badge_label(appearance.get("badge")))
        class_portraits = {
            label.replace("Féminin", tr("Féminin")).replace("Masculin", tr("Masculin")): path
            for label, path in bundled_portrait_choices().items()
        }
        class_portrait_var = StringVar(value=tr("Portrait de classe…"))

        win = Toplevel(self.root)
        win.title(f"Personnaliser — {window.pseudo}")
        win.transient(self.root)
        win.grab_set()
        win.resizable(False, False)
        content = TtkFrame(win, padding=14)
        content.pack(fill="both", expand=True)
        content.columnconfigure(1, weight=1)

        preview = TkLabel(content, width=96, height=96, borderwidth=0)
        preview.grid(row=0, column=0, rowspan=4, padx=(0, 12), pady=(0, 8))
        preview_photo: ImageTk.PhotoImage | None = None

        TtkLabel(content, text=f"{window.pseudo} · {window.character_class or 'classe inconnue'}").grid(
            row=0, column=1, columnspan=2, sticky="w", pady=(0, 8)
        )
        TtkLabel(content, text="Alias").grid(row=1, column=1, sticky="w", padx=(0, 8), pady=3)
        TtkEntry(content, textvariable=alias_var, width=30).grid(row=1, column=2, sticky="ew", pady=3)
        TtkLabel(content, text="Icône").grid(row=2, column=1, sticky="w", padx=(0, 8), pady=3)
        badge_combo = Combobox(
            content,
            values=tuple(item[0] for item in BADGE_CATALOG.values()),
            state="readonly",
            textvariable=badge_var,
            width=25,
        )
        badge_combo.grid(row=2, column=2, sticky="ew", pady=3)

        def refresh_preview(*_args) -> None:
            nonlocal preview_photo
            palette = resolved_theme_palette(self.root, self.settings.theme)
            avatar = build_avatar_image(
                window.pseudo,
                portrait_data=portrait_data,
                badge=badge_from_label(badge_var.get()),
                size=96,
                background=palette["bg3"],
                foreground=palette["on_dark"],
                show_badge=True,
            )
            preview_photo = ImageTk.PhotoImage(avatar, master=win)
            preview.configure(image=preview_photo, background=palette["bg2"])

        def choose_portrait() -> None:
            nonlocal portrait_data
            path = filedialog.askopenfilename(
                title="Choisir un portrait",
                filetypes=[
                    ("Images", "*.png *.jpg *.jpeg *.webp *.bmp"),
                    ("Tous les fichiers", "*.*"),
                ],
                parent=win,
            )
            if not path:
                return
            try:
                portrait_data = encode_portrait_file(path)
            except ValueError as exc:
                messagebox.showerror("Portrait incompatible", str(exc), parent=win)
                return
            refresh_preview()

        def remove_portrait() -> None:
            nonlocal portrait_data
            portrait_data = ""
            refresh_preview()

        portrait_buttons = TtkFrame(content)
        portrait_buttons.grid(row=3, column=1, columnspan=2, sticky="ew", pady=(5, 8))
        TtkButton(portrait_buttons, text="Choisir un portrait…", command=choose_portrait).pack(
            side="left", fill="x", expand=True, padx=(0, 3)
        )
        TtkButton(portrait_buttons, text="Retirer", command=remove_portrait).pack(
            side="left", padx=(3, 0)
        )
        class_portrait_combo = Combobox(
            content,
            values=tuple(class_portraits),
            state="readonly",
            textvariable=class_portrait_var,
            width=30,
        )
        class_portrait_combo.grid(row=4, column=1, columnspan=2, sticky="ew", pady=(0, 8))

        def choose_class_portrait(_event=None) -> None:
            nonlocal portrait_data
            path = class_portraits.get(class_portrait_var.get())
            if not path:
                return
            try:
                portrait_data = encode_portrait_file(path)
            except ValueError as exc:
                messagebox.showerror("Portrait incompatible", str(exc), parent=win)
                return
            refresh_preview()

        class_portrait_combo.bind("<<ComboboxSelected>>", choose_class_portrait)
        TtkLabel(
            content,
            text=(
                "Le portrait personnel est recadré et enregistré localement. Les illustrations "
                "et icônes de jeu intégrées sont la propriété d’Ankama Games. Dofus Window "
                "Manager est un projet communautaire non affilié à Ankama."
            ),
            style="Muted.TLabel",
            wraplength=430,
            justify="left",
        ).grid(row=5, column=0, columnspan=3, sticky="w", pady=(2, 10))

        def apply() -> None:
            alias = alias_var.get().strip()
            if alias:
                self.aliases[window.pseudo] = alias
            else:
                self.aliases.pop(window.pseudo, None)

            visuals = dict(self.character_visuals)
            badge = badge_from_label(badge_var.get())
            if portrait_data or badge != "none":
                visuals[window.pseudo] = {"portrait": portrait_data, "badge": badge}
            else:
                visuals.pop(window.pseudo, None)
            self.character_visuals = sanitize_character_visuals(visuals)
            profile_saved = self._save_active_profile_customizations()
            self.update_listboxes()
            if profile_saved:
                self._log(
                    f"Apparence de {window.pseudo} mise à jour dans le profil "
                    f"'{self._active_profile_name}'"
                )
            else:
                self._log(
                    f"Apparence de {window.pseudo} appliquée en mémoire — "
                    "enregistrez un profil pour la conserver"
                )
            win.destroy()

        badge_combo.bind("<<ComboboxSelected>>", refresh_preview)
        refresh_preview()
        buttons = TtkFrame(content)
        buttons.grid(row=6, column=0, columnspan=3, sticky="e")
        TtkButton(buttons, text="Annuler", command=win.destroy).pack(side="right")
        TtkButton(buttons, text="Appliquer", command=apply, style="Accent.TButton").pack(
            side="right", padx=(0, 6)
        )

    def rename_alias(self):
        hwnd = self._selected_managed_hwnd()
        if hwnd is None:
            return
        w = self._all_windows.get(hwnd)
        if not w:
            return
        current = self.aliases.get(w.pseudo, "")
        new = simpledialog.askstring(
            "Alias facultatif",
            (
                f"Alias pour {w.pseudo} :\n\n"
                "Exemples : Terre, Feu, Eau, Air, Mineur, Alchimiste…\n"
                "Laissez le champ vide pour supprimer l’alias."
            ),
            initialvalue=current,
            parent=self.root,
        )
        if new is None:
            return
        alias = new.strip()
        if alias:
            self.aliases[w.pseudo] = alias
            self._log(f"Alias « {alias} » défini pour {w.pseudo}")
        else:
            self.aliases.pop(w.pseudo, None)
            self._log(f"Alias supprimé pour {w.pseudo}")
        if not self._save_active_profile_customizations():
            self._log("Enregistrez un profil pour conserver cet alias")
        self.update_listboxes()

    def apply_order_by_pseudo(self, pseudos: list[str]):
        # Build mapping pseudo -> list of hwnds
        buckets: dict[str, list[int]] = {}
        for hwnd in self._managed_order:
            w = self._all_windows.get(hwnd)
            if not w:
                continue
            buckets.setdefault(w.pseudo, []).append(hwnd)

        new_order: list[int] = []
        used = set()

        for p in pseudos:
            lst = buckets.get(p, [])
            for hwnd in lst:
                if hwnd not in used:
                    new_order.append(hwnd)
                    used.add(hwnd)

        # Append remaining managed
        for hwnd in self._managed_order:
            if hwnd not in used:
                new_order.append(hwnd)
                used.add(hwnd)

        self._managed_order = new_order
        self.rotation_index = 0
        self._sync_streamdeck_order_with_managed()

    # ---------------------------- Settings ----------------------------

    def open_settings_window(self):
        win = Toplevel(self.root)
        win.title("Paramètres")
        win.transient(self.root)
        win.grab_set()
        win.resizable(True, True)
        settings_height = max(560, min(820, self.root.winfo_screenheight() - 120))
        win.geometry(f"650x{settings_height}")

        localized_overlay_labels = {field: tr(label) for field, label in OVERLAY_FIELD_LABELS.items()}
        localized_position_labels = {anchor: tr(label) for anchor, label in SWAP_POSITION_LABELS.items()}
        selected_theme_label = theme_label(self.settings.theme, self.game_mode)
        theme_var = StringVar(value=selected_theme_label)
        refresh_var = StringVar(value=str(self.settings.refresh_seconds))
        hk_fwd = StringVar(value=self.settings.hotkeys.get("forward", "F5"))
        hk_bwd = StringVar(value=self.settings.hotkeys.get("backward", "F6"))
        hk_ign = StringVar(value=self.settings.hotkeys.get("ignore", "F7"))
        hk_attention = StringVar(value=self.settings.hotkeys.get("next_attention", "F8"))
        hk_ref = StringVar(value=self.settings.hotkeys.get("refresh", "Ctrl+Alt+R"))
        direct_hotkeys = [
            StringVar(value=self.settings.hotkeys.get(f"window_{position}", ""))
            for position in range(1, 9)
        ]
        evt_hook = BooleanVar(value=bool(getattr(self.settings, "event_hook_enabled", True)))
        popup_watch = BooleanVar(value=bool(getattr(self.settings, "popup_watch_enabled", False)))
        minimize_to_tray = BooleanVar(value=bool(self.settings.minimize_to_tray))
        start_with_windows = BooleanVar(value=bool(self.settings.start_with_windows))
        check_updates = BooleanVar(value=bool(self.settings.check_updates_automatically))
        include_prereleases = BooleanVar(value=bool(self.settings.include_prereleases))
        swap_notification = BooleanVar(value=bool(self.settings.swap_notification_enabled))
        swap_position = StringVar(
            value=localized_position_labels.get(self.settings.swap_notification_anchor, tr("En haut au centre"))
        )
        swap_duration = StringVar(value=str(self.settings.swap_notification_duration_ms))
        swap_opacity = StringVar(value=str(self.settings.swap_notification_opacity))
        notification_layout = dict(
            self.settings.swap_notification_layout or DEFAULT_ROTATION_OVERLAY_LAYOUT
        )
        notification_left = StringVar(
            value=localized_overlay_labels.get(notification_layout["left"], tr("Numéro"))
        )
        notification_line1 = StringVar(
            value=localized_overlay_labels.get(notification_layout["line1"], tr("Nom"))
        )
        notification_line2_left = StringVar(
            value=localized_overlay_labels.get(notification_layout["line2_left"], tr("Classe"))
        )
        notification_line2_right = StringVar(
            value=localized_overlay_labels.get(notification_layout["line2_right"], tr("Alias"))
        )
        rotation_overlay = BooleanVar(value=bool(self.settings.rotation_overlay_enabled))
        overlay_opacity = StringVar(value=str(self.settings.rotation_overlay_opacity))
        overlay_x = StringVar(value=str(self.settings.rotation_overlay_x))
        overlay_y = StringVar(value=str(self.settings.rotation_overlay_y))
        overlay_locked = BooleanVar(value=bool(self.settings.rotation_overlay_locked))
        overlay_width = StringVar(value=str(self.settings.rotation_overlay_width))
        overlay_auto_width = BooleanVar(value=bool(self.settings.rotation_overlay_auto_width))
        overlay_height = StringVar(value=str(self.settings.rotation_overlay_height))
        overlay_orientation = StringVar(
            value=(
                "Horizontal"
                if self.settings.rotation_overlay_orientation == "horizontal"
                else "Vertical"
            )
        )
        show_portraits = BooleanVar(value=bool(self.settings.show_character_portraits))
        show_popup_portraits = BooleanVar(value=bool(self.settings.show_popup_portraits))
        show_popup_badges = BooleanVar(value=bool(self.settings.show_popup_badges))
        show_overlay_portraits = BooleanVar(value=bool(self.settings.show_overlay_portraits))
        show_overlay_badges = BooleanVar(value=bool(self.settings.show_overlay_badges))
        attention_blink = BooleanVar(value=bool(self.settings.attention_blink_enabled))
        show_badges = BooleanVar(value=bool(self.settings.show_character_badges))
        overlay_layout = dict(
            self.settings.rotation_overlay_layout or DEFAULT_ROTATION_OVERLAY_LAYOUT
        )
        overlay_left = StringVar(
            value=localized_overlay_labels.get(overlay_layout["left"], tr("Numéro"))
        )
        overlay_line1 = StringVar(
            value=localized_overlay_labels.get(overlay_layout["line1"], tr("Nom"))
        )
        overlay_line2_left = StringVar(
            value=localized_overlay_labels.get(overlay_layout["line2_left"], tr("Classe"))
        )
        overlay_line2_right = StringVar(
            value=localized_overlay_labels.get(overlay_layout["line2_right"], tr("Alias"))
        )

        available_theme_ids = theme_ids_for_mode(self.game_mode)
        theme_labels = [THEME_LABELS[theme_id] for theme_id in available_theme_ids]

        settings_footer = TtkFrame(win, padding=(12, 8))
        settings_footer.pack(side="bottom", fill="x")
        settings_notebook = Notebook(win)
        settings_notebook.pack(fill="both", expand=True, padx=12, pady=(10, 0))
        tab_canvases: dict[str, Canvas] = {}

        def create_scrollable_tab(label: str) -> TtkFrame:
            tab = TtkFrame(settings_notebook)
            settings_notebook.add(tab, text=tr(label))
            viewport = TtkFrame(tab)
            viewport.pack(fill="both", expand=True)
            canvas = Canvas(
                viewport,
                borderwidth=0,
                highlightthickness=0,
                background=resolved_theme_palette(self.root, self.settings.theme)["bg"],
            )
            scrollbar = Scrollbar(viewport, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            content = TtkFrame(canvas, padding=12)
            content_window = canvas.create_window((0, 0), window=content, anchor="nw")
            content.bind(
                "<Configure>",
                lambda _event, target=canvas: target.configure(
                    scrollregion=target.bbox("all")
                ),
            )
            canvas.bind(
                "<Configure>",
                lambda event, target=canvas, item=content_window: target.itemconfigure(
                    item,
                    width=event.width,
                ),
            )
            tab_canvases[str(tab)] = canvas
            return content

        general_content = create_scrollable_tab("Général")
        appearance_content = create_scrollable_tab("Apparence")
        shortcuts_content = create_scrollable_tab("Raccourcis")

        def scroll_active_tab(event) -> None:
            canvas = tab_canvases.get(settings_notebook.select())
            if canvas is not None:
                canvas.yview_scroll(wheel_scroll_units(event.delta), "units")

        win.bind("<MouseWheel>", scroll_active_tab)

        general = TtkLabelFrame(
            general_content,
            text=tr("Général · mode {game}", game=self.game_label),
            padding=10,
        )
        general.pack(fill="x", pady=(0, 8))
        general.columnconfigure(1, weight=1)
        TtkLabel(general, text="Intervalle d’actualisation").grid(
            row=0, column=0, sticky="w", padx=(0, 12), pady=4
        )
        refresh_row = TtkFrame(general)
        refresh_row.grid(row=0, column=1, sticky="w", pady=4)
        Spinbox(refresh_row, from_=2, to=300, textvariable=refresh_var, width=6).pack(side="left")
        TtkLabel(refresh_row, text=" secondes", style="Muted.TLabel").pack(side="left")
        TtkCheckbutton(
            general,
            text="Réduire dans la zone de notification à la fermeture",
            variable=minimize_to_tray,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 2))
        TtkCheckbutton(
            general,
            text="Lancer avec Windows, directement dans la zone de notification",
            variable=start_with_windows,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=2)
        TtkCheckbutton(
            general,
            text="Rechercher automatiquement les mises à jour officielles",
            variable=check_updates,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 2))
        TtkCheckbutton(
            general,
            text="Inclure les versions bêta",
            variable=include_prereleases,
        ).grid(row=4, column=0, columnspan=2, sticky="w", padx=(22, 0), pady=2)
        TtkLabel(
            general,
            text="Vérification quotidienne au maximum ; aucun téléchargement automatique.",
            style="Muted.TLabel",
        ).grid(row=5, column=0, columnspan=2, sticky="w", padx=(22, 0), pady=(0, 4))

        theme_section = TtkLabelFrame(
            appearance_content,
            text=tr("Thème · mode {game}", game=self.game_label),
            padding=10,
        )
        theme_section.pack(fill="x", pady=(0, 8))
        theme_section.columnconfigure(1, weight=1)
        TtkLabel(theme_section, text="Thème").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=4,
        )
        Combobox(
            theme_section,
            values=theme_labels,
            state="readonly",
            textvariable=theme_var,
        ).grid(row=0, column=1, sticky="ew", pady=4)

        attention_display = TtkLabelFrame(
            appearance_content,
            text="Demandes d’attention",
            padding=10,
        )
        attention_display.pack(fill="x", pady=(0, 8))
        TtkCheckbutton(
            attention_display,
            text="Clignotement léger sur l’application, l’overlay et le Stream Deck",
            variable=attention_blink,
        ).pack(anchor="w")
        TtkLabel(
            attention_display,
            text="Désactivez le clignotement pour conserver uniquement la couleur orange et le repère !.",
            style="Muted.TLabel",
            wraplength=560,
        ).pack(anchor="w", padx=(22, 0), pady=(3, 0))

        in_game_display = TtkLabelFrame(
            appearance_content,
            text=tr("Affichage en jeu · {game}", game=self.game_label),
            padding=10,
        )
        in_game_display.pack(fill="x", pady=(0, 8))
        in_game_display.columnconfigure(1, weight=1)
        TtkCheckbutton(
            in_game_display,
            text="Afficher le personnage après chaque changement de fenêtre",
            variable=swap_notification,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        TtkLabel(in_game_display, text="Position de la notification").grid(
            row=1, column=0, sticky="w", padx=(22, 12), pady=3
        )
        Combobox(
            in_game_display,
            values=tuple(localized_position_labels.values()),
            state="readonly",
            textvariable=swap_position,
            width=23,
        ).grid(row=1, column=1, sticky="ew", pady=3)
        TtkLabel(in_game_display, text="Durée").grid(
            row=2, column=0, sticky="w", padx=(22, 12), pady=3
        )
        duration_row = TtkFrame(in_game_display)
        duration_row.grid(row=2, column=1, sticky="w", pady=3)
        Spinbox(duration_row, from_=600, to=5000, increment=100, textvariable=swap_duration, width=7).pack(
            side="left"
        )
        TtkLabel(duration_row, text=" ms", style="Muted.TLabel").pack(side="left")
        TtkLabel(duration_row, text="   Opacité", style="Muted.TLabel").pack(side="left")
        Spinbox(duration_row, from_=35, to=100, textvariable=swap_opacity, width=5).pack(side="left")
        TtkLabel(duration_row, text=" %", style="Muted.TLabel").pack(side="left")

        notification_content = TtkLabelFrame(
            in_game_display,
            text="Contenu de la notification",
            padding=8,
        )
        notification_content.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=(22, 0),
            pady=(7, 3),
        )
        notification_content.columnconfigure(1, weight=1)
        notification_content.columnconfigure(3, weight=1)
        overlay_field_values = tuple(localized_overlay_labels.values())
        notification_slots = (
            ("À gauche", notification_left, "Ligne 1", notification_line1),
            (
                "Ligne 2 · gauche",
                notification_line2_left,
                "Ligne 2 · droite",
                notification_line2_right,
            ),
        )
        for row_index, (left_label, left_var, right_label, right_var) in enumerate(notification_slots):
            TtkLabel(notification_content, text=left_label).grid(
                row=row_index, column=0, sticky="w", padx=(0, 6), pady=3
            )
            Combobox(
                notification_content,
                values=overlay_field_values,
                state="readonly",
                textvariable=left_var,
                width=10,
            ).grid(row=row_index, column=1, sticky="ew", padx=(0, 12), pady=3)
            TtkLabel(notification_content, text=right_label).grid(
                row=row_index, column=2, sticky="w", padx=(0, 6), pady=3
            )
            Combobox(
                notification_content,
                values=overlay_field_values,
                state="readonly",
                textvariable=right_var,
                width=10,
            ).grid(row=row_index, column=3, sticky="ew", pady=3)

        TtkCheckbutton(
            in_game_display,
            text="Afficher en permanence la rotation",
            variable=rotation_overlay,
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 3))
        TtkLabel(in_game_display, text="Opacité").grid(
            row=5, column=0, sticky="w", padx=(22, 12), pady=3
        )
        opacity_row = TtkFrame(in_game_display)
        opacity_row.grid(row=5, column=1, sticky="w", pady=3)
        Spinbox(opacity_row, from_=35, to=100, textvariable=overlay_opacity, width=7).pack(side="left")
        TtkLabel(opacity_row, text=" %", style="Muted.TLabel").pack(side="left")
        TtkLabel(opacity_row, text=tr("   Orientation"), style="Muted.TLabel").pack(side="left")
        Combobox(
            opacity_row,
            values=(tr("Vertical"), tr("Horizontal")),
            state="readonly",
            textvariable=overlay_orientation,
            width=11,
        ).pack(side="left")
        TtkLabel(in_game_display, text="Position X / Y").grid(
            row=6, column=0, sticky="w", padx=(22, 12), pady=3
        )
        position_row = TtkFrame(in_game_display)
        position_row.grid(row=6, column=1, sticky="w", pady=3)
        Spinbox(position_row, from_=-10000, to=10000, textvariable=overlay_x, width=7).pack(side="left")
        TtkLabel(position_row, text=" / ", style="Muted.TLabel").pack(side="left")
        Spinbox(position_row, from_=-10000, to=10000, textvariable=overlay_y, width=7).pack(side="left")

        TtkLabel(in_game_display, text="Largeur manuelle / hauteur").grid(
            row=7, column=0, sticky="w", padx=(22, 12), pady=3
        )
        size_row = TtkFrame(in_game_display)
        size_row.grid(row=7, column=1, sticky="w", pady=3)
        Spinbox(size_row, from_=80, to=1800, textvariable=overlay_width, width=7).pack(side="left")
        TtkLabel(size_row, text=" / ", style="Muted.TLabel").pack(side="left")
        Spinbox(size_row, from_=0, to=1600, textvariable=overlay_height, width=7).pack(side="left")
        TtkLabel(size_row, text=" px · hauteur 0 = automatique", style="Muted.TLabel").pack(side="left")
        TtkCheckbutton(
            in_game_display,
            text="Adapter automatiquement la largeur de l’overlay au contenu",
            variable=overlay_auto_width,
        ).grid(row=8, column=0, columnspan=2, sticky="w", padx=(22, 0), pady=(2, 4))

        overlay_content = TtkLabelFrame(
            in_game_display,
            text="Contenu de l’overlay",
            padding=8,
        )
        overlay_content.grid(
            row=9,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=(22, 0),
            pady=(7, 3),
        )
        overlay_content.columnconfigure(1, weight=1)
        overlay_content.columnconfigure(3, weight=1)
        overlay_slots = (
            ("À gauche", overlay_left, "Ligne 1", overlay_line1),
            ("Ligne 2 · gauche", overlay_line2_left, "Ligne 2 · droite", overlay_line2_right),
        )
        for row_index, (left_label, left_var, right_label, right_var) in enumerate(overlay_slots):
            TtkLabel(overlay_content, text=left_label).grid(
                row=row_index,
                column=0,
                sticky="w",
                padx=(0, 6),
                pady=3,
            )
            Combobox(
                overlay_content,
                values=overlay_field_values,
                state="readonly",
                textvariable=left_var,
                width=10,
            ).grid(row=row_index, column=1, sticky="ew", padx=(0, 12), pady=3)
            TtkLabel(overlay_content, text=right_label).grid(
                row=row_index,
                column=2,
                sticky="w",
                padx=(0, 6),
                pady=3,
            )
            Combobox(
                overlay_content,
                values=overlay_field_values,
                state="readonly",
                textvariable=right_var,
                width=10,
            ).grid(row=row_index, column=3, sticky="ew", pady=3)
        TtkLabel(
            overlay_content,
            text="Par défaut : numéro à gauche, nom ligne 1, puis classe · alias ligne 2.",
            style="Muted.TLabel",
        ).grid(row=2, column=0, columnspan=4, sticky="w", pady=(5, 0))

        TtkCheckbutton(
            in_game_display,
            text="Verrouiller et ignorer les clics",
            variable=overlay_locked,
        ).grid(row=10, column=0, columnspan=2, sticky="w", padx=(22, 0), pady=(4, 2))
        TtkLabel(
            in_game_display,
            text=(
                "Déverrouillé : glissez l’en-tête pour déplacer l’overlay, une ligne pour la "
                "réordonner, ou la poignée ◢ pour le redimensionner."
            ),
            style="Muted.TLabel",
            wraplength=560,
        ).grid(row=11, column=0, columnspan=2, sticky="w", padx=(22, 0), pady=(0, 2))
        TtkCheckbutton(
            in_game_display,
            text="Afficher les portraits dans la notification",
            variable=show_popup_portraits,
        ).grid(row=12, column=0, columnspan=2, sticky="w", padx=(22, 0), pady=(6, 2))
        TtkCheckbutton(
            in_game_display,
            text="Afficher les icônes dans la notification",
            variable=show_popup_badges,
        ).grid(row=13, column=0, columnspan=2, sticky="w", padx=(22, 0), pady=2)
        TtkCheckbutton(
            in_game_display,
            text="Afficher les portraits dans l’overlay",
            variable=show_overlay_portraits,
        ).grid(row=14, column=0, columnspan=2, sticky="w", padx=(22, 0), pady=2)
        TtkCheckbutton(
            in_game_display,
            text="Afficher les icônes dans l’overlay",
            variable=show_overlay_badges,
        ).grid(row=15, column=0, columnspan=2, sticky="w", padx=(22, 0), pady=2)
        TtkCheckbutton(
            in_game_display,
            text="Afficher les portraits sur le Stream Deck",
            variable=show_portraits,
        ).grid(row=16, column=0, columnspan=2, sticky="w", padx=(22, 0), pady=2)
        TtkCheckbutton(
            in_game_display,
            text="Afficher les icônes officielles de caractéristiques ou de métiers sur le Stream Deck",
            variable=show_badges,
        ).grid(row=17, column=0, columnspan=2, sticky="w", padx=(22, 0), pady=2)

        hotkeys = TtkLabelFrame(shortcuts_content, text="Raccourcis clavier", padding=10)
        hotkeys.pack(fill="x", pady=(0, 8))
        hotkeys.columnconfigure(1, weight=1)
        hotkey_rows = (
            ("Personnage suivant", hk_fwd),
            ("Personnage précédent", hk_bwd),
            ("Ignorer la fenêtre", hk_ign),
            ("Prochaine fenêtre en attente", hk_attention),
            ("Actualiser la liste", hk_ref),
        )
        for row_index, (label, variable) in enumerate(hotkey_rows):
            TtkLabel(hotkeys, text=label).grid(row=row_index, column=0, sticky="w", padx=(0, 12), pady=3)
            TtkEntry(hotkeys, textvariable=variable, width=22).grid(
                row=row_index, column=1, sticky="ew", pady=3
            )
        TtkLabel(
            hotkeys,
            text="Exemples : F5, Ctrl+Alt+R, Shift+F6 ou Win+F7",
            style="Muted.TLabel",
        ).grid(row=len(hotkey_rows), column=0, columnspan=2, sticky="w", pady=(6, 0))
        direct_start_row = len(hotkey_rows) + 1
        TtkLabel(
            hotkeys,
            text=tr("Accès direct par position (facultatif)"),
            style="Header.TLabel",
        ).grid(row=direct_start_row, column=0, columnspan=2, sticky="w", pady=(12, 4))
        for offset, variable in enumerate(direct_hotkeys, start=1):
            TtkLabel(hotkeys, text=tr("Fenêtre {position}", position=offset)).grid(
                row=direct_start_row + offset,
                column=0,
                sticky="w",
                padx=(0, 12),
                pady=3,
            )
            TtkEntry(hotkeys, textvariable=variable, width=22).grid(
                row=direct_start_row + offset,
                column=1,
                sticky="ew",
                pady=3,
            )
        TtkLabel(
            hotkeys,
            text=tr("Raccourcis globaux. Laissez vide pour désactiver. Exemple : 1 → première fenêtre."),
            style="Muted.TLabel",
        ).grid(
            row=direct_start_row + len(direct_hotkeys) + 1,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(5, 0),
        )

        detection = TtkLabelFrame(general_content, text="Détection des fenêtres", padding=10)
        detection.pack(fill="x")
        TtkCheckbutton(
            detection,
            text="Synchronisation en temps réel et détection des demandes d’attention Windows",
            variable=evt_hook,
        ).pack(anchor="w")

        # This Retro-only option is intentionally absent in Unity mode.
        if self.game_mode == "retro":
            popup_label = "Rotation automatique sur les invitations de groupe ou d’échange"
            if not _POPUP_WATCH_AVAILABLE:
                popup_label += " — module optionnel absent"
            popup_button = TtkCheckbutton(detection, text=popup_label, variable=popup_watch)
            popup_button.pack(anchor="w", pady=(4, 0))
            if not _POPUP_WATCH_AVAILABLE:
                popup_button.configure(state="disabled")

        def apply():
            selected_theme = theme_var.get().strip()
            new_theme = next(
                (
                    theme_id
                    for theme_id in available_theme_ids
                    if THEME_LABELS[theme_id] == selected_theme
                ),
                default_theme_for_mode(self.game_mode),
            )
            try:
                overlay_x_value = int(overlay_x.get())
                overlay_y_value = int(overlay_y.get())
                overlay_width_value = max(80, min(1800, int(overlay_width.get())))
                requested_height = int(overlay_height.get())
                overlay_height_value = 0 if requested_height <= 0 else max(80, min(1600, requested_height))
            except ValueError:
                messagebox.showerror(
                    "Géométrie de l’overlay",
                    "Les positions et dimensions de l’overlay doivent être des nombres entiers.",
                    parent=win,
                )
                return
            try:
                self._apply_runtime_theme(new_theme)
            except Exception:
                messagebox.showwarning("Thème", f"Thème non disponible: {new_theme}")

            try:
                sec = int(refresh_var.get())
                self.settings.refresh_seconds = max(2, min(300, sec))
            except Exception:
                self.settings.refresh_seconds = 10

            # Validate hotkeys early (gives immediate feedback)
            fwd = hk_fwd.get().strip() or "F5"
            bwd = hk_bwd.get().strip() or "F6"
            ign = hk_ign.get().strip() or "F7"
            next_attention = hk_attention.get().strip() or "F8"
            ref = hk_ref.get().strip() or "Ctrl+Alt+R"
            direct_specs = [variable.get().strip() for variable in direct_hotkeys]
            try:
                parsed_hotkeys: dict[tuple[int, int], str] = {}
                named_specs = [
                    ("Personnage suivant", fwd),
                    ("Personnage précédent", bwd),
                    ("Ignorer la fenêtre", ign),
                    ("Prochaine fenêtre en attente", next_attention),
                    ("Actualiser la liste", ref),
                    *(
                        (f"Fenêtre {position}", spec)
                        for position, spec in enumerate(direct_specs, start=1)
                        if spec
                    ),
                ]
                for label, spec in named_specs:
                    parsed = parse_hotkey(spec)
                    duplicate = parsed_hotkeys.get(parsed)
                    if duplicate is not None:
                        raise ValueError(
                            f"Le raccourci {spec} est utilisé à la fois pour « {duplicate} » et « {label} »."
                        )
                    parsed_hotkeys[parsed] = label
            except ValueError as e:
                messagebox.showerror("Hotkeys", str(e))
                return

            self.settings.hotkeys["forward"] = fwd
            self.settings.hotkeys["backward"] = bwd
            self.settings.hotkeys["ignore"] = ign
            self.settings.hotkeys["next_attention"] = next_attention
            self.settings.hotkeys["refresh"] = ref
            for position, spec in enumerate(direct_specs, start=1):
                self.settings.hotkeys[f"window_{position}"] = spec

            self.settings.event_hook_enabled = bool(evt_hook.get())
            requested_startup = bool(start_with_windows.get())
            if requested_startup != self.settings.start_with_windows:
                try:
                    set_startup_enabled(requested_startup)
                except OSError as exc:
                    messagebox.showerror("Démarrage Windows", str(exc), parent=win)
                    return
            self.settings.start_with_windows = requested_startup
            self.settings.minimize_to_tray = bool(minimize_to_tray.get())
            updates_were_disabled = not self.settings.check_updates_automatically
            self.settings.check_updates_automatically = bool(check_updates.get())
            self.settings.include_prereleases = bool(include_prereleases.get())
            self.settings.swap_notification_enabled = bool(swap_notification.get())
            selected_position = swap_position.get().strip()
            self.settings.swap_notification_anchor = next(
                (
                    value
                    for value, label in localized_position_labels.items()
                    if label == selected_position
                ),
                "top_center",
            )
            self.settings.swap_notification_duration_ms = clamp_notification_duration(swap_duration.get())
            self.settings.swap_notification_opacity = clamp_overlay_opacity(swap_opacity.get())
            reverse_overlay_fields = {
                label: field for field, label in localized_overlay_labels.items()
            }
            self.settings.swap_notification_layout = {
                "left": reverse_overlay_fields.get(notification_left.get(), "position"),
                "line1": reverse_overlay_fields.get(notification_line1.get(), "name"),
                "line2_left": reverse_overlay_fields.get(notification_line2_left.get(), "class"),
                "line2_right": reverse_overlay_fields.get(notification_line2_right.get(), "alias"),
            }
            self.settings.rotation_overlay_enabled = bool(rotation_overlay.get())
            self.settings.rotation_overlay_opacity = clamp_overlay_opacity(overlay_opacity.get())
            self.settings.rotation_overlay_x = overlay_x_value
            self.settings.rotation_overlay_y = overlay_y_value
            self.settings.rotation_overlay_width = overlay_width_value
            self.settings.rotation_overlay_auto_width = bool(overlay_auto_width.get())
            self.settings.rotation_overlay_height = overlay_height_value
            self.settings.rotation_overlay_orientation = normalize_overlay_orientation(
                overlay_orientation.get()
            )
            self.settings.rotation_overlay_locked = bool(overlay_locked.get())
            self.settings.rotation_overlay_layout = {
                "left": reverse_overlay_fields.get(overlay_left.get(), "position"),
                "line1": reverse_overlay_fields.get(overlay_line1.get(), "name"),
                "line2_left": reverse_overlay_fields.get(overlay_line2_left.get(), "class"),
                "line2_right": reverse_overlay_fields.get(overlay_line2_right.get(), "alias"),
            }
            self.settings.show_character_portraits = bool(show_portraits.get())
            self.settings.show_popup_portraits = bool(show_popup_portraits.get())
            self.settings.show_popup_badges = bool(show_popup_badges.get())
            self.settings.show_overlay_portraits = bool(show_overlay_portraits.get())
            self.settings.show_overlay_badges = bool(show_overlay_badges.get())
            self.settings.attention_blink_enabled = bool(attention_blink.get())
            self.settings.show_character_badges = bool(show_badges.get())
            self.settings.remember_display_preferences(self.game_mode)

            # Keep the remembered Retro preference untouched while configuring Unity.
            if self.game_mode == "retro":
                self._set_popup_watch_enabled(bool(popup_watch.get()))

            # Start/stop WinEventHook immediately for convenience.
            if self.settings.event_hook_enabled:
                self._start_win_event_hook()
            else:
                self._stop_win_event_hook()

            try:
                self._register_hotkeys()
                # If Windows refuses a hotkey (already in use, etc.), show it quickly.
                self.root.after(250, self._report_hotkey_error_popup)
            except Exception as e:
                messagebox.showerror("Hotkeys", f"Impossible d'appliquer les hotkeys: {e}")
                return

            save_settings(self.settings_path, self.settings)
            self._apply_display_preferences()
            self._attention_blink_phase = True
            self._apply_attention_blink_visuals()
            self._publish_streamdeck_state()
            self._log("Paramètres appliqués")
            win.destroy()
            if updates_were_disabled and self.settings.check_updates_automatically:
                self.root.after(100, self._check_updates_on_startup)

        def reset_display_from_settings() -> None:
            if self.reset_display_settings(parent=win):
                win.destroy()

        TtkButton(
            settings_footer,
            text="Réinitialiser l’affichage…",
            command=reset_display_from_settings,
        ).pack(side="left")
        TtkButton(settings_footer, text="Annuler", command=win.destroy).pack(side="right")
        TtkButton(settings_footer, text="Appliquer", command=apply, style="Accent.TButton").pack(
            side="right", padx=(0, 6)
        )

    def _report_hotkey_error_popup(self):
        try:
            err = self.hotkeys.consume_last_error()
            if err:
                messagebox.showwarning("Hotkeys", err)
        except Exception:
            pass

    # ---------------------------- Popup watcher (Retro) ----------------------------

    def _set_popup_watch_enabled(self, enabled: bool):
        """Enable/disable the Retro in-game popup watcher."""
        self._popup_watch_enabled = bool(enabled)
        try:
            self.settings.popup_watch_enabled = self._popup_watch_enabled
        except Exception:
            pass

        if self.game_mode != "retro":
            return

        # Lazy-init if user enables it later
        if self._popup_watch_enabled and self.popup_watcher is None and _POPUP_WATCH_AVAILABLE:
            try:
                self.popup_watcher = RetroPopupWatcher(
                    emit=lambda evt: self._popup_queue.put(evt),
                    max_fps_per_window=4.0,
                    cooldown_sec=2.0,
                )
                self.popup_watcher.set_enabled(True)
                self._ensure_popup_event_pump()
            except Exception as e:
                try:
                    self.logger.error("PopupWatcher init failed", e)
                except Exception:
                    pass
                self._log(f"PopupWatcher: impossible de démarrer ({e})")
                self.popup_watcher = None
                return

        if self.popup_watcher is not None:
            try:
                self.popup_watcher.set_enabled(self._popup_watch_enabled)
            except Exception:
                pass
            if self._popup_watch_enabled:
                self._update_popup_watcher_targets()
            else:
                # Release Graphics Capture sessions while the option is disabled.
                try:
                    self.popup_watcher.update_targets([])
                except Exception:
                    pass
            try:
                self._log(f"PopupWatch enabled: {self._popup_watch_enabled}")
            except Exception:
                pass

    def _ensure_popup_event_pump(self) -> None:
        if self._popup_event_pump_started:
            return
        self._popup_event_pump_started = True
        self.root.after(50, self._process_popup_events)

    def _shutdown_popup_watcher(self) -> None:
        watcher = self.popup_watcher
        self.popup_watcher = None
        if watcher is None:
            return
        try:
            watcher.shutdown()
        except Exception:
            pass

    def _update_popup_watcher_targets(self):
        """Update the watcher target windows (managed order)."""
        if self.popup_watcher is None:
            return
        if not getattr(self, "_popup_watch_enabled", False):
            # Keep targets untouched while disabled to avoid capture churn.
            return

        targets = []
        for hwnd in list(self._managed_order):
            if hwnd in self._ignored:
                continue
            w = self._all_windows.get(hwnd)
            if not w:
                continue

            # Prefer the current Win32 title; fall back to the cached title.
            title = (get_window_title(int(hwnd)) or w.title or "").strip()

            if not title:
                continue

            targets.append(WatchedWindow(hwnd=int(hwnd), title=title))

        try:
            self.popup_watcher.update_targets(targets)
            # Keep a short target summary in the UI log for diagnostics.
            sample = ", ".join([t.title for t in targets[:3]])
            more = " ..." if len(targets) > 3 else ""
            self._log(f"PopupWatch targets: {len(targets)} [{sample}{more}]")
        except Exception as e:
            try:
                self._log(f"PopupWatch update_targets FAILED: {repr(e)}")
            except Exception:
                pass
            try:
                self.logger.error("PopupWatch update_targets failed", e)
            except Exception:
                pass

    def _process_popup_events(self):
        """Poll popup events emitted by the watcher; runs on Tk thread."""
        # If app is closing, stop polling
        if self._stop_event.is_set():
            return

        while True:
            try:
                evt = self._popup_queue.get_nowait()
            except Exception:
                break

            try:
                self.logger.action(f"Popup detected -> focusing | hwnd={evt.hwnd} | title={evt.title}")
            except Exception:
                pass

            try:
                self._handle_popup_event(evt)
            except Exception:
                pass

        # keep polling
        self.root.after(50, self._process_popup_events)

    def _handle_popup_event(self, evt: PopupEvent) -> None:
        if not self._popup_watch_enabled:
            return

        hwnd = int(evt.hwnd)
        if hwnd not in self._managed_order or hwnd in self._ignored:
            return

        # Avoid ping-pong when several clients display a popup together.
        now = time.monotonic()
        if now < self._popup_global_cooldown_until:
            return

        try:
            self.rotation_index = self._managed_order.index(hwnd)
            focus_hwnd(hwnd)
            self._record_character_focus(hwnd, notify=True)
            self._popup_global_cooldown_until = now + self._popup_global_cooldown_sec
            self._log(f"Popup détecté → focus {evt.title}")
        except (FocusError, ValueError) as exc:
            self._log(f"PopupWatch focus échoué: {exc}")

    def _register_hotkeys(self):
        # IDs must be stable
        try:
            self.hotkeys.set_hotkey(1, self.settings.hotkeys.get("forward", "F5"), lambda: self.root.after(0, lambda: self.request_rotation("forward")))
            self.hotkeys.set_hotkey(2, self.settings.hotkeys.get("backward", "F6"), lambda: self.root.after(0, lambda: self.request_rotation("backward")))
            self.hotkeys.set_hotkey(3, self.settings.hotkeys.get("ignore", "F7"), lambda: self.root.after(0, self.ignore_selected))
            self.hotkeys.set_hotkey(4, self.settings.hotkeys.get("refresh", "Ctrl+Alt+R"), lambda: self.root.after(0, lambda: self.refresh_windows(quiet=True, force=True)))
            self.hotkeys.set_hotkey(5, self.settings.hotkeys.get("next_attention", "F8"), lambda: self.root.after(0, lambda: self.focus_next_attention(source="Raccourci")))
            direct_labels: list[str] = []
            for position in range(1, 9):
                hotkey_id = 100 + position
                self.hotkeys.clear_hotkey(hotkey_id)
                spec = self.settings.hotkeys.get(f"window_{position}", "").strip()
                if not spec:
                    continue
                self.hotkeys.set_hotkey(
                    hotkey_id,
                    spec,
                    lambda target=position: self.root.after(
                        0,
                        lambda: self.focus_managed_position(target),
                    ),
                )
                direct_labels.append(f"{position}={spec}")
            self._log(
                f"Hotkeys: {self.settings.hotkeys.get('forward')} / {self.settings.hotkeys.get('backward')} / {self.settings.hotkeys.get('ignore')} / {self.settings.hotkeys.get('next_attention')} / {self.settings.hotkeys.get('refresh')}"
                + (f" / accès direct: {', '.join(direct_labels)}" if direct_labels else "")
            )
        except Exception as e:
            self._log(f"Hotkeys non appliqués: {e}")

    def _check_hotkey_errors(self):
        if self._stop_event.is_set():
            return

        # Watchdog: restart the listener if it stopped.
        try:
            if not self.hotkeys.is_alive():
                if not self._hotkey_dead_logged:
                    self._log("Hotkeys: listener arrêté, redémarrage…")
                    self._hotkey_dead_logged = True
                self.hotkeys.start()
                self._register_hotkeys()
            else:
                self._hotkey_dead_logged = False
        except Exception:
            pass
        try:
            err = self.hotkeys.consume_last_error()
            if err:
                self._log(f"Hotkeys: {err}")
        except Exception:
            pass
        self.root.after(1000, self._check_hotkey_errors)

# ---------------------------- Lifecycle ----------------------------

    def on_close(self, *, force: bool = False):
        if not force and self.settings.minimize_to_tray and self.tray.is_running:
            self._hide_main_window()
            return

        self._stop_event.set()
        try:
            self.settings.auto_refresh = bool(self.auto_refresh_enabled.get())
            self.settings.last_profile = self.selected_profile.get().strip()
            save_settings(self.settings_path, self.settings)
        except Exception:
            pass

        try:
            if self.streamdeck_bridge is not None:
                self.streamdeck_bridge.stop()
        except Exception:
            pass

        try:
            self.hotkeys.stop()
        except Exception:
            pass

        self._stop_win_event_hook()
        self._shutdown_popup_watcher()
        try:
            self.overlay_ui.close_all()
        except Exception:
            pass

        self.tray.stop()

        self.root.destroy()


    def run(self):
        self.root.mainloop()


# -------- JSON helpers (avoid unicode issues) --------


def json_dump(obj: object) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def json_load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run(game_mode: str = "unity", *, start_minimized: bool = False) -> None:
    app = WindowManagerApp(game_mode=game_mode, start_minimized=start_minimized)
    # Auto-load last profile if available
    last = app.selected_profile.get().strip()
    if last:
        try:
            pr = load_profile(app.dirs["profiles"], last)
            app._apply_loaded_profile(pr)
            app._log(f"Profil auto-chargé: '{last}'")
        except Exception:
            pass
    app.run()
