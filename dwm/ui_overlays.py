from __future__ import annotations

import ctypes
import os
from collections.abc import Callable, Mapping, Sequence
from ctypes import wintypes
from tkinter import Frame as TkFrame
from tkinter import Label as TkLabel
from tkinter import Toplevel
from tkinter.ttk import Button as TtkButton
from tkinter.ttk import Frame as TtkFrame
from tkinter.ttk import Treeview

from PIL import ImageTk

from .services.display_overlay import (
    CharacterDisplay,
    calculate_overlay_text_scale,
    DEFAULT_ROTATION_OVERLAY_LAYOUT,
    clamp_notification_duration,
    clamp_overlay_opacity,
    compose_overlay_row,
    format_tk_geometry,
    normalize_overlay_layout,
    place_inside_rect,
)
from .services.character_visuals import build_avatar_image, build_badge_tile_image


DEFAULT_PALETTE = {
    "bg": "#0f1724",
    "bg2": "#172131",
    "bg3": "#223047",
    "fg": "#e8eef7",
    "muted": "#9aa9bd",
    "line": "#33435b",
    "accent": "#22b8f0",
    "on_dark": "#ffffff",
    "on_accent": "#ffffff",
    "attention": "#f59e0b",
    "on_attention": "#111827",
}


def _blend_hex(foreground: str, background: str, ratio: float) -> str:
    try:
        ratio = max(0.0, min(1.0, float(ratio)))
        fg = tuple(int(foreground[index : index + 2], 16) for index in (1, 3, 5))
        bg = tuple(int(background[index : index + 2], 16) for index in (1, 3, 5))
        mixed = tuple(round(a * ratio + b * (1.0 - ratio)) for a, b in zip(fg, bg))
        return "#" + "".join(f"{value:02x}" for value in mixed)
    except (TypeError, ValueError):
        return foreground


def _get_window_rect(hwnd: int) -> tuple[int, int, int, int] | None:
    if os.name != "nt" or not hwnd:
        return None

    class Rect(ctypes.Structure):
        _fields_ = (
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        )

    try:
        user32 = ctypes.windll.user32
        user32.GetWindowRect.argtypes = (wintypes.HWND, ctypes.POINTER(Rect))
        user32.GetWindowRect.restype = wintypes.BOOL
        rect = Rect()
        if not user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(rect)):
            return None
        return int(rect.left), int(rect.top), int(rect.right), int(rect.bottom)
    except Exception:
        return None


def _apply_non_activating_style(window: Toplevel, *, click_through: bool) -> None:
    if os.name != "nt":
        return

    try:
        window.update_idletasks()
        user32 = ctypes.windll.user32
        raw_hwnd = wintypes.HWND(int(window.winfo_id()))
        user32.GetAncestor.argtypes = (wintypes.HWND, wintypes.UINT)
        user32.GetAncestor.restype = wintypes.HWND
        hwnd = user32.GetAncestor(raw_hwnd, 2) or raw_hwnd  # GA_ROOT
        getter = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
        setter = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
        getter.argtypes = (wintypes.HWND, ctypes.c_int)
        getter.restype = ctypes.c_ssize_t
        setter.argtypes = (wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t)
        setter.restype = ctypes.c_ssize_t

        gwl_exstyle = -20
        ws_ex_toolwindow = 0x00000080
        ws_ex_transparent = 0x00000020
        ws_ex_noactivate = 0x08000000
        style = int(getter(hwnd, gwl_exstyle))
        style |= ws_ex_toolwindow | ws_ex_noactivate
        if click_through:
            style |= ws_ex_transparent
        else:
            style &= ~ws_ex_transparent
        setter(hwnd, gwl_exstyle, style)

        hwnd_topmost = wintypes.HWND(-1)
        swp_nomove = 0x0002
        swp_nosize = 0x0001
        swp_noactivate = 0x0010
        swp_showwindow = 0x0040
        swp_framechanged = 0x0020
        user32.SetWindowPos.argtypes = (
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        )
        user32.SetWindowPos.restype = wintypes.BOOL
        user32.SetWindowPos(
            hwnd,
            hwnd_topmost,
            0,
            0,
            0,
            0,
            swp_nomove | swp_nosize | swp_noactivate | swp_showwindow | swp_framechanged,
        )
    except Exception:
        return


class OverlayUI:
    """Own the compact manager, swap notification and persistent rotation overlay."""

    def __init__(
        self,
        root,
        *,
        focus_character: Callable[[int], None],
        save_overlay_position: Callable[[int, int], None],
        save_compact_geometry: Callable[[str], None],
        save_overlay_size: Callable[[int, int], None] | None = None,
        reorder_character: Callable[[int, str | int], None] | None = None,
        palette: Mapping[str, str] | None = None,
    ) -> None:
        self.root = root
        self.focus_character = focus_character
        self.save_overlay_position = save_overlay_position
        self.save_compact_geometry = save_compact_geometry
        self.save_overlay_size = save_overlay_size or (lambda _width, _height: None)
        self.reorder_character = reorder_character or (lambda _hwnd, _direction: None)
        self.palette = dict(DEFAULT_PALETTE)
        if palette:
            self.palette.update(palette)

        self.entries: list[CharacterDisplay] = []
        self.toast_window: Toplevel | None = None
        self.toast_job: str | None = None
        self.persistent_window: Toplevel | None = None
        self.compact_window: Toplevel | None = None
        self.compact_tree: Treeview | None = None

        self.persistent_enabled = False
        self.persistent_x = 24
        self.persistent_y = 160
        self.persistent_opacity = 88
        self.persistent_locked = False
        self.persistent_layout = dict(DEFAULT_ROTATION_OVERLAY_LAYOUT)
        self.persistent_width = 300
        self.persistent_height = 0
        self.show_portraits = True
        self.show_badges = True
        self.attention_blink_enabled = True
        self.attention_blink_phase = True
        self._persistent_images: list[ImageTk.PhotoImage] = []
        self._toast_images: list[ImageTk.PhotoImage] = []
        self._drag_pointer: tuple[int, int] | None = None
        self._drag_window_origin: tuple[int, int] | None = None
        self._drag_distance = 0
        self._drag_target_hwnd: int | None = None
        self._resize_pointer: tuple[int, int] | None = None
        self._resize_window_size: tuple[int, int] | None = None
        self._persistent_rows: dict[int, TkFrame] = {}
        self._persistent_text_widgets: list[tuple[object, int, bool]] = []
        self._drop_target_index: int | None = None
        self._drop_preview_hwnd: int | None = None

    @property
    def compact_is_open(self) -> bool:
        return self.compact_window is not None and bool(self.compact_window.winfo_exists())

    @property
    def has_visible_character_list(self) -> bool:
        return self.persistent_enabled or self.compact_is_open

    def set_palette(self, palette: Mapping[str, str]) -> None:
        self.palette = dict(DEFAULT_PALETTE)
        self.palette.update(palette)
        if self.persistent_window is not None:
            self._destroy_persistent()
            if self.persistent_enabled:
                self._ensure_persistent()
                self._render_persistent()
        if self.compact_window is not None:
            try:
                self.compact_window.configure(background=self.palette["bg"])
            except Exception:
                pass
        self._refresh_compact()

    def update_characters(self, entries: Sequence[CharacterDisplay]) -> None:
        self.entries = list(entries)
        if self.persistent_enabled:
            self._ensure_persistent()
            self._render_persistent()
        self._refresh_compact()

    def _attention_background(self) -> str:
        if not self.attention_blink_enabled or self.attention_blink_phase:
            return self.palette["attention"]
        return _blend_hex(self.palette["attention"], self.palette["bg2"], 0.68)

    def set_attention_blink(self, *, enabled: bool, phase: bool) -> None:
        self.attention_blink_enabled = bool(enabled)
        self.attention_blink_phase = bool(phase)
        color = self._attention_background()
        if self.compact_tree is not None:
            self.compact_tree.tag_configure(
                "attention",
                background=color,
                foreground=self.palette["on_attention"],
            )
        attention_hwnds = {entry.hwnd for entry in self.entries if entry.attention}
        for hwnd in attention_hwnds:
            row = self._persistent_rows.get(hwnd)
            if row is not None:
                self._configure_widget_colors(row, color, self.palette["on_attention"])

    def _configure_widget_colors(self, widget, background: str, foreground: str) -> None:
        try:
            widget.configure(background=background)
        except Exception:
            pass
        try:
            widget.configure(foreground=foreground)
        except Exception:
            pass
        try:
            children = widget.winfo_children()
        except Exception:
            children = ()
        for child in children:
            self._configure_widget_colors(child, background, foreground)

    # ---------------------------- Compact manager ----------------------------

    def open_compact(self, geometry: str = "") -> None:
        if self.compact_is_open:
            self.compact_window.lift()
            return

        self.root.withdraw()
        window = Toplevel(self.root)
        self.compact_window = window
        window.title("Dofus Window Manager — Mode compact")
        window.attributes("-topmost", True)
        window.minsize(280, 120)
        if geometry:
            try:
                window.geometry(geometry)
            except Exception:
                window.geometry("340x260+40+120")
        else:
            height = max(140, min(380, 54 + len(self.entries) * 31))
            window.geometry(f"340x{height}+40+120")

        toolbar = TtkFrame(window, padding=(6, 6, 6, 0))
        toolbar.pack(fill="x")
        TtkButton(
            toolbar,
            text="Quitter le mode compact",
            command=self.close_compact,
        ).pack(side="right")

        tree = Treeview(window, show="tree", selectmode="browse")
        self.compact_tree = tree
        tree.column("#0", width=310, minwidth=220, stretch=True)
        tree.pack(fill="both", expand=True, padx=6, pady=6)
        tree.bind("<Double-1>", self._activate_compact_selection)
        tree.bind("<Return>", self._activate_compact_selection)
        window.protocol("WM_DELETE_WINDOW", self.close_compact)
        self._refresh_compact()

    def close_compact(self, *, show_root: bool = True) -> None:
        window = self.compact_window
        self.compact_window = None
        self.compact_tree = None
        if window is not None:
            try:
                self.save_compact_geometry(window.geometry())
            except Exception:
                pass
            try:
                window.destroy()
            except Exception:
                pass
        if show_root:
            try:
                self.root.deiconify()
                self.root.state("normal")
                self.root.lift()
                self.root.focus_force()
            except Exception:
                pass

    def _refresh_compact(self) -> None:
        tree = self.compact_tree
        if tree is None or not self.compact_is_open:
            return
        children = tree.get_children()
        if children:
            tree.delete(*children)
        tree.tag_configure(
            "active",
            background=self.palette["accent"],
            foreground=self.palette["on_accent"],
        )
        tree.tag_configure(
            "attention",
            background=self._attention_background(),
            foreground=self.palette["on_attention"],
        )
        tree.tag_configure("normal", background=self.palette["bg2"], foreground=self.palette["fg"])
        if not self.entries:
            tree.insert("", "end", text="Aucune fenêtre en rotation", tags=("normal",))
            return
        for entry in self.entries:
            details = entry.character_class
            if entry.alias:
                details = f"{entry.pseudo} · {entry.character_class}".strip(" ·")
            suffix = f"  —  {details}" if details else ""
            tree.insert(
                "",
                "end",
                iid=str(entry.hwnd),
                text=(
                    f"{'!  ' if entry.attention else ''}{entry.position}.  "
                    f"{entry.primary_text}{suffix}"
                ),
                tags=("attention" if entry.attention else "active" if entry.active else "normal",),
            )
        active = next((entry for entry in self.entries if entry.active), None)
        if active is not None:
            tree.selection_set(str(active.hwnd))
            tree.see(str(active.hwnd))

    def _activate_compact_selection(self, _event=None) -> None:
        tree = self.compact_tree
        if tree is None:
            return
        selection = tree.selection()
        if not selection:
            return
        try:
            hwnd = int(selection[0])
        except ValueError:
            return
        self.focus_character(hwnd)

    # ---------------------------- Persistent overlay ----------------------------

    def configure_persistent(
        self,
        *,
        enabled: bool,
        x: int,
        y: int,
        opacity: int,
        locked: bool,
        layout: Mapping[str, str] | None = None,
        width: int = 300,
        height: int = 0,
        show_portrait: bool = True,
        show_badge: bool = True,
    ) -> None:
        recreate = self.persistent_locked != bool(locked)
        self.persistent_enabled = bool(enabled)
        self.persistent_x = int(x)
        self.persistent_y = int(y)
        self.persistent_opacity = clamp_overlay_opacity(opacity)
        self.persistent_locked = bool(locked)
        self.persistent_layout = normalize_overlay_layout(layout)
        self.persistent_width = max(240, min(900, int(width)))
        requested_height = int(height)
        self.persistent_height = 0 if requested_height <= 0 else max(80, min(1600, requested_height))
        self.show_portraits = bool(show_portrait)
        self.show_badges = bool(show_badge)

        if not self.persistent_enabled:
            self._destroy_persistent()
            return
        if recreate:
            self._destroy_persistent()
        self._ensure_persistent()
        self._render_persistent()

    def _ensure_persistent(self) -> None:
        if self.persistent_window is not None and self.persistent_window.winfo_exists():
            return
        window = Toplevel(self.root)
        self.persistent_window = window
        window.withdraw()
        window.overrideredirect(True)
        window.attributes("-topmost", True)
        window.attributes("-alpha", self.persistent_opacity / 100)
        window.configure(background=self.palette["line"])
        initial_height = self.persistent_height if self.persistent_height > 0 else 80
        window.geometry(
            format_tk_geometry(
                self.persistent_width,
                initial_height,
                self.persistent_x,
                self.persistent_y,
            )
        )
        window.update_idletasks()
        _apply_non_activating_style(window, click_through=self.persistent_locked)
        window.deiconify()

    def _destroy_persistent(self) -> None:
        window = self.persistent_window
        self.persistent_window = None
        self._persistent_rows.clear()
        self._persistent_text_widgets.clear()
        self._persistent_images.clear()
        self._drop_target_index = None
        self._drop_preview_hwnd = None
        if window is not None:
            try:
                window.destroy()
            except Exception:
                pass

    def _render_persistent(self) -> None:
        window = self.persistent_window
        if window is None:
            return
        for child in window.winfo_children():
            child.destroy()
        self._persistent_images.clear()
        self._persistent_rows.clear()
        self._persistent_text_widgets.clear()
        self._drop_target_index = None
        self._drop_preview_hwnd = None

        body = TkFrame(window, background=self.palette["bg"], padx=2, pady=2)
        body.pack(fill="both", expand=True, padx=1, pady=1)
        if not self.persistent_locked:
            header = TkLabel(
                body,
                text="ROTATION  ·  déplacer ici  ·  glisser une ligne = ordre",
                background=self.palette["bg3"],
                foreground=self.palette["on_dark"],
                anchor="w",
                padx=9,
                pady=4,
                font=("Segoe UI", 8, "bold"),
            )
            header.pack(fill="x")
            self._register_scaled_text(header, 8, bold=True)
            self._bind_drag(header, None)

        if not self.entries:
            empty = TkLabel(
                body,
                text="Aucune fenêtre en rotation",
                background=self.palette["bg2"],
                foreground=self.palette["muted"],
                padx=10,
                pady=10,
            )
            empty.pack(fill="x")
            self._register_scaled_text(empty, 10)
            if not self.persistent_locked:
                self._bind_drag(empty, None)
        else:
            for entry in self.entries:
                if entry.attention:
                    background = self._attention_background()
                    foreground = self.palette["on_attention"]
                elif entry.active:
                    background = self.palette["accent"]
                    foreground = self.palette["on_accent"]
                else:
                    background = self.palette["bg2"]
                    foreground = self.palette["fg"]
                row = TkFrame(
                    body,
                    background=background,
                    padx=8,
                    pady=4,
                    highlightthickness=0,
                    highlightbackground=self.palette["accent"],
                )
                row.pack(
                    fill="both" if self.persistent_height > 0 else "x",
                    expand=self.persistent_height > 0,
                    pady=(1, 0),
                )
                self._persistent_rows[entry.hwnd] = row
                left_text, primary_text, secondary_text = compose_overlay_row(
                    entry,
                    self.persistent_layout,
                )
                attention_marker = None
                if entry.attention:
                    attention_marker = TkLabel(
                        row,
                        text="!",
                        width=2,
                        background=background,
                        foreground=foreground,
                        anchor="center",
                        font=("Segoe UI", 12, "bold"),
                    )
                    attention_marker.pack(side="left")
                    self._register_scaled_text(attention_marker, 12, bold=True)
                portrait = None
                if self.show_portraits or (self.show_badges and entry.badge != "none"):
                    if self.show_portraits:
                        avatar = build_avatar_image(
                            entry.pseudo,
                            portrait_data=entry.portrait_data,
                            badge=entry.badge,
                            size=40,
                            background=self.palette["bg3"],
                            foreground=self.palette["on_dark"],
                            show_badge=self.show_badges,
                        )
                    else:
                        avatar = build_badge_tile_image(
                            entry.badge,
                            size=40,
                            background=self.palette["bg3"],
                        )
                    photo = ImageTk.PhotoImage(avatar, master=window)
                    self._persistent_images.append(photo)
                    portrait = TkLabel(
                        row,
                        image=photo,
                        background=background,
                        borderwidth=0,
                        padx=0,
                        pady=0,
                    )
                    portrait.pack(side="left", padx=(0, 6))
                position = None
                if left_text:
                    position = TkLabel(
                        row,
                        text=left_text,
                        width=(3 if self.persistent_layout["left"] == "position" else 12),
                        background=background,
                        foreground=foreground,
                        anchor="center",
                        font=("Segoe UI", 10, "bold"),
                    )
                    position.pack(side="left")
                    self._register_scaled_text(position, 10, bold=True)
                texts = TkFrame(row, background=background)
                texts.pack(side="left", fill="x", expand=True)
                primary = None
                if primary_text:
                    primary = TkLabel(
                        texts,
                        text=primary_text,
                        background=background,
                        foreground=foreground,
                        anchor="w",
                        font=("Segoe UI", 10, "bold"),
                    )
                    primary.pack(fill="x")
                    self._register_scaled_text(primary, 10, bold=True)
                secondary = None
                if secondary_text:
                    secondary = TkLabel(
                        texts,
                        text=secondary_text,
                        background=background,
                        foreground=(
                            foreground
                            if entry.active or entry.attention
                            else self.palette["muted"]
                        ),
                        anchor="w",
                        font=("Segoe UI", 8),
                    )
                    secondary.pack(fill="x")
                    self._register_scaled_text(secondary, 8)
                if not self.persistent_locked:
                    controls = TkFrame(row, background=background)
                    controls.pack(side="right", padx=(4, 0))
                    up = TkLabel(
                        controls,
                        text="▲",
                        background=background,
                        foreground=foreground,
                        cursor="hand2",
                        padx=3,
                    )
                    down = TkLabel(
                        controls,
                        text="▼",
                        background=background,
                        foreground=foreground,
                        cursor="hand2",
                        padx=3,
                    )
                    up.pack(side="left")
                    down.pack(side="left")
                    self._register_scaled_text(up, 10, bold=True)
                    self._register_scaled_text(down, 10, bold=True)
                    up.bind(
                        "<Button-1>",
                        lambda _event, target=entry.hwnd: self.reorder_character(target, "up"),
                    )
                    down.bind(
                        "<Button-1>",
                        lambda _event, target=entry.hwnd: self.reorder_character(target, "down"),
                    )
                    for widget in (
                        row,
                        attention_marker,
                        portrait,
                        position,
                        texts,
                        primary,
                        secondary,
                    ):
                        if widget is None:
                            continue
                        self._bind_drag(widget, entry.hwnd)

        window.update_idletasks()
        width = self.persistent_width
        height = self.persistent_height if self.persistent_height > 0 else max(46, window.winfo_reqheight())
        window.geometry(format_tk_geometry(width, height, self.persistent_x, self.persistent_y))
        self._apply_persistent_text_scale(width, height)
        window.attributes("-alpha", self.persistent_opacity / 100)
        _apply_non_activating_style(window, click_through=self.persistent_locked)
        if not self.persistent_locked:
            grip = TkLabel(
                window,
                text="◢",
                background=self.palette["bg3"],
                foreground=self.palette["on_dark"],
                cursor="size_nw_se",
                padx=2,
                pady=1,
            )
            grip.place(relx=1.0, rely=1.0, anchor="se")
            grip.bind("<ButtonPress-1>", self._resize_start)
            grip.bind("<B1-Motion>", self._resize_motion)
            grip.bind("<ButtonRelease-1>", self._resize_release)

    def _persistent_scale(self, width: int, height: int) -> float:
        return calculate_overlay_text_scale(
            width,
            height,
            len(self.entries),
            locked=self.persistent_locked,
            fixed_height=self.persistent_height > 0,
        )

    def _register_scaled_text(self, widget, base_size: int, *, bold: bool = False) -> None:
        self._persistent_text_widgets.append((widget, int(base_size), bool(bold)))

    def _apply_persistent_text_scale(self, width: int, height: int) -> None:
        scale = self._persistent_scale(width, height)
        for widget, base_size, bold in tuple(self._persistent_text_widgets):
            try:
                size = max(6, min(30, round(base_size * scale)))
                widget.configure(font=("Segoe UI", size, "bold" if bold else "normal"))
            except Exception:
                continue

    def _bind_drag(self, widget, hwnd: int | None) -> None:
        widget.bind("<ButtonPress-1>", lambda event, target=hwnd: self._drag_start(event, target))
        widget.bind("<B1-Motion>", self._drag_motion)
        widget.bind("<ButtonRelease-1>", self._drag_release)

    def _drag_start(self, event, hwnd: int | None) -> None:
        window = self.persistent_window
        if window is None:
            return
        self._drag_pointer = (int(event.x_root), int(event.y_root))
        self._drag_window_origin = (window.winfo_x(), window.winfo_y())
        self._drag_distance = 0
        self._drag_target_hwnd = hwnd

    def _drag_motion(self, event) -> None:
        window = self.persistent_window
        if window is None or self._drag_pointer is None or self._drag_window_origin is None:
            return
        delta_x = int(event.x_root) - self._drag_pointer[0]
        delta_y = int(event.y_root) - self._drag_pointer[1]
        self._drag_distance = max(self._drag_distance, abs(delta_x) + abs(delta_y))
        if self._drag_target_hwnd is not None:
            if self._drag_distance >= 5:
                self._update_drop_preview(int(event.y_root))
            return
        self.persistent_x = self._drag_window_origin[0] + delta_x
        self.persistent_y = self._drag_window_origin[1] + delta_y
        window.geometry(format_tk_geometry(window.winfo_width(), window.winfo_height(), self.persistent_x, self.persistent_y))

    def _drag_release(self, _event) -> None:
        target = self._drag_target_hwnd
        clicked = self._drag_distance < 5 and target is not None
        destination = self._drop_target_index
        self._drag_pointer = None
        self._drag_window_origin = None
        self._drag_target_hwnd = None
        self._clear_drop_preview()
        if clicked:
            self.focus_character(target)
        elif target is not None and destination is not None:
            self.reorder_character(target, destination)
        elif target is None:
            self.save_overlay_position(self.persistent_x, self.persistent_y)

    def _update_drop_preview(self, pointer_y: int) -> None:
        if not self.entries:
            return
        insertion_index = len(self.entries)
        preview_hwnd = self.entries[-1].hwnd
        for index, entry in enumerate(self.entries):
            row = self._persistent_rows.get(entry.hwnd)
            if row is None:
                continue
            midpoint = row.winfo_rooty() + row.winfo_height() // 2
            if pointer_y < midpoint:
                insertion_index = index
                preview_hwnd = entry.hwnd
                break

        source_index = next(
            (index for index, entry in enumerate(self.entries) if entry.hwnd == self._drag_target_hwnd),
            None,
        )
        if source_index is None:
            return
        if insertion_index > source_index:
            insertion_index -= 1
        insertion_index = max(0, min(len(self.entries) - 1, insertion_index))

        if preview_hwnd != self._drop_preview_hwnd:
            self._clear_drop_preview()
            row = self._persistent_rows.get(preview_hwnd)
            if row is not None:
                row.configure(highlightthickness=2, highlightbackground=self.palette["attention"])
            self._drop_preview_hwnd = preview_hwnd
        self._drop_target_index = insertion_index

    def _clear_drop_preview(self) -> None:
        if self._drop_preview_hwnd is not None:
            row = self._persistent_rows.get(self._drop_preview_hwnd)
            if row is not None:
                try:
                    row.configure(highlightthickness=0)
                except Exception:
                    pass
        self._drop_preview_hwnd = None
        self._drop_target_index = None

    def _resize_start(self, event) -> None:
        window = self.persistent_window
        if window is None:
            return
        self._resize_pointer = (int(event.x_root), int(event.y_root))
        self._resize_window_size = (window.winfo_width(), window.winfo_height())

    def _resize_motion(self, event) -> None:
        window = self.persistent_window
        if window is None or self._resize_pointer is None or self._resize_window_size is None:
            return
        width = max(240, min(900, self._resize_window_size[0] + int(event.x_root) - self._resize_pointer[0]))
        height = max(80, min(1600, self._resize_window_size[1] + int(event.y_root) - self._resize_pointer[1]))
        self.persistent_width = width
        self.persistent_height = height
        window.geometry(format_tk_geometry(width, height, self.persistent_x, self.persistent_y))
        self._apply_persistent_text_scale(width, height)

    def _resize_release(self, _event) -> None:
        self._resize_pointer = None
        self._resize_window_size = None
        self.save_overlay_size(self.persistent_width, self.persistent_height)
        self._render_persistent()

    # ---------------------------- Swap notification ----------------------------

    def show_swap_notification(
        self,
        entry: CharacterDisplay,
        *,
        anchor: str,
        duration_ms: int,
        opacity: int = 96,
        layout: Mapping[str, str] | None = None,
        show_portrait: bool = True,
        show_badge: bool = True,
    ) -> None:
        self.hide_swap_notification()
        window = Toplevel(self.root)
        self.toast_window = window
        window.withdraw()
        window.overrideredirect(True)
        window.attributes("-topmost", True)
        window.attributes("-alpha", clamp_overlay_opacity(opacity) / 100)
        window.configure(background=self.palette["accent"])

        body = TkFrame(window, background=self.palette["bg"], padx=12, pady=9)
        body.pack(fill="both", expand=True, padx=2, pady=2)
        self._toast_images.clear()
        if show_portrait or (show_badge and entry.badge != "none"):
            if show_portrait:
                avatar = build_avatar_image(
                    entry.pseudo,
                    portrait_data=entry.portrait_data,
                    badge=entry.badge,
                    size=64,
                    background=self.palette["bg3"],
                    foreground=self.palette["on_dark"],
                    show_badge=show_badge,
                )
            else:
                avatar = build_badge_tile_image(
                    entry.badge,
                    size=64,
                    background=self.palette["bg3"],
                )
            photo = ImageTk.PhotoImage(avatar, master=window)
            self._toast_images.append(photo)
            TkLabel(
                body,
                image=photo,
                background=self.palette["bg"],
                borderwidth=0,
            ).pack(side="left", padx=(0, 10))

        left_text, primary_text, secondary_text = compose_overlay_row(entry, layout)
        if left_text:
            TkLabel(
                body,
                text=left_text,
                width=3 if normalize_overlay_layout(layout)["left"] == "position" else 11,
                background=self.palette["bg3"],
                foreground=self.palette["on_dark"],
                anchor="center",
                font=("Segoe UI", 13, "bold"),
                padx=4,
                pady=7,
            ).pack(side="left", fill="y", padx=(0, 10))

        text_box = TkFrame(body, background=self.palette["bg"])
        text_box.pack(side="left", fill="both", expand=True)
        if primary_text:
            TkLabel(
                text_box,
                text=primary_text,
                background=self.palette["bg"],
                foreground=self.palette["fg"],
                anchor="w",
                font=("Segoe UI", 17, "bold"),
            ).pack(fill="x", expand=True)
        if secondary_text:
            TkLabel(
                text_box,
                text=secondary_text,
                background=self.palette["bg"],
                foreground=self.palette["muted"],
                anchor="w",
                font=("Segoe UI", 10),
            ).pack(fill="x", expand=True)

        width, height = 420, 94
        target_rect = _get_window_rect(entry.hwnd)
        if target_rect is None:
            target_rect = (0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight())
        x, y = place_inside_rect(target_rect, (width, height), anchor)
        window.geometry(format_tk_geometry(width, height, x, y))
        window.update_idletasks()
        _apply_non_activating_style(window, click_through=True)
        window.deiconify()
        self.toast_job = self.root.after(
            clamp_notification_duration(duration_ms),
            self.hide_swap_notification,
        )

    def hide_swap_notification(self) -> None:
        if self.toast_job is not None:
            try:
                self.root.after_cancel(self.toast_job)
            except Exception:
                pass
            self.toast_job = None
        window = self.toast_window
        self.toast_window = None
        self._toast_images.clear()
        if window is not None:
            try:
                window.destroy()
            except Exception:
                pass

    def close_all(self) -> None:
        self.hide_swap_notification()
        self._destroy_persistent()
        self.close_compact(show_root=False)
