from __future__ import annotations

import tkinter as tk
from tkinter import StringVar, Toplevel, messagebox as native_messagebox
from tkinter.ttk import Button, Entry, Frame, Label

from .services.i18n import tr
from .ui_design import (
    DANGER_BUTTON_STYLE,
    PRIMARY_BUTTON_STYLE,
    SECONDARY_BUTTON_STYLE,
    UI,
)
from .ui_windowing import schedule_center_window


def _prepare_dialog(parent, title: str) -> tuple[Toplevel, Frame]:
    win = Toplevel(parent)
    win.title(title)
    win.transient(parent)
    win.resizable(False, False)

    body = Frame(win, padding=UI.window_padding)
    body.pack(fill="both", expand=True)
    return win, body


def _finish_dialog_layout(win: Toplevel, parent, width: int) -> None:
    try:
        win.update_idletasks()
        height = max(1, int(win.winfo_reqheight()))
        win.geometry(f"{width}x{height}")
    except Exception:
        pass
    schedule_center_window(win, parent)


def _run_modal(win: Toplevel, parent) -> None:
    previous_grab = None
    try:
        previous_grab = parent.grab_current()
    except Exception:
        pass
    try:
        win.wait_visibility()
    except Exception:
        pass
    try:
        win.grab_set()
    except Exception:
        pass
    try:
        win.focus_force()
    except Exception:
        pass
    parent.wait_window(win)
    if previous_grab is not None and previous_grab is not win:
        try:
            exists = getattr(previous_grab, "winfo_exists", None)
            if not callable(exists) or exists():
                previous_grab.grab_set()
        except Exception:
            pass


def show_message(
    parent,
    title: str,
    message: str,
    *,
    heading: str | None = None,
    button_text: str = "OK",
    kind: str = "info",
) -> None:
    win, body = _prepare_dialog(parent, title)
    heading_style = {
        "warning": "Warning.TLabel",
        "error": "DangerHeader.TLabel",
    }.get(kind, "Header.TLabel")
    Label(
        body,
        text=heading or title,
        style=heading_style,
    ).pack(anchor="w")
    Label(
        body,
        text=message,
        style="Muted.TLabel",
        wraplength=450,
        justify="left",
    ).pack(anchor="w", pady=(6, 18))

    footer = Frame(body)
    footer.pack(fill="x")
    Button(
        footer,
        text=button_text,
        command=win.destroy,
        style=PRIMARY_BUTTON_STYLE,
    ).pack(side="right")

    win.bind("<Return>", lambda _event: win.destroy())
    win.bind("<Escape>", lambda _event: win.destroy())
    _finish_dialog_layout(win, parent, UI.dialog_width)
    _run_modal(win, parent)


def ask_confirmation(
    parent,
    title: str,
    message: str,
    *,
    heading: str | None = None,
    confirm_text: str = "Confirmer",
    cancel_text: str = "Annuler",
    danger: bool = False,
) -> bool:
    win, body = _prepare_dialog(parent, title)
    result = {"accepted": False}

    Label(
        body,
        text=heading or title,
        style="Header.TLabel",
    ).pack(anchor="w")
    Label(
        body,
        text=message,
        style="Muted.TLabel",
        wraplength=470,
        justify="left",
    ).pack(anchor="w", pady=(6, 18))

    def accept() -> None:
        result["accepted"] = True
        win.destroy()

    footer = Frame(body)
    footer.pack(fill="x")
    Button(
        footer,
        text=confirm_text,
        command=accept,
        style=DANGER_BUTTON_STYLE if danger else PRIMARY_BUTTON_STYLE,
    ).pack(side="right")
    Button(
        footer,
        text=cancel_text,
        command=win.destroy,
        style=SECONDARY_BUTTON_STYLE,
    ).pack(side="right", padx=(0, 8))

    win.bind("<Return>", lambda _event: accept())
    win.bind("<Escape>", lambda _event: win.destroy())
    _finish_dialog_layout(win, parent, UI.confirmation_width)
    _run_modal(win, parent)
    return bool(result["accepted"])


def ask_text(
    parent,
    title: str,
    prompt: str,
    *,
    initial: str = "",
    confirm_text: str = "Enregistrer",
    cancel_text: str = "Annuler",
    allow_empty: bool = False,
) -> str | None:
    win, body = _prepare_dialog(parent, title)
    value = StringVar(value=initial)
    result: dict[str, str | None] = {"value": None}

    Label(body, text=title, style="Header.TLabel").pack(anchor="w")
    Label(
        body,
        text=prompt,
        style="Muted.TLabel",
        wraplength=450,
        justify="left",
    ).pack(anchor="w", pady=(6, 8))

    entry = Entry(body, textvariable=value)
    entry.pack(fill="x", pady=(0, 18))

    def accept() -> None:
        candidate = value.get().strip()
        if not candidate and not allow_empty:
            try:
                entry.focus_set()
            except Exception:
                pass
            return
        result["value"] = candidate
        win.destroy()

    footer = Frame(body)
    footer.pack(fill="x")
    Button(
        footer,
        text=confirm_text,
        command=accept,
        style=PRIMARY_BUTTON_STYLE,
    ).pack(side="right")
    Button(
        footer,
        text=cancel_text,
        command=win.destroy,
        style=SECONDARY_BUTTON_STYLE,
    ).pack(side="right", padx=(0, 8))

    win.bind("<Return>", lambda _event: accept())
    win.bind("<Escape>", lambda _event: win.destroy())
    try:
        entry.selection_range(0, "end")
        entry.focus_set()
    except Exception:
        pass
    _finish_dialog_layout(win, parent, UI.dialog_width)
    _run_modal(win, parent)
    return result["value"]


def _resolve_parent(parent):
    return parent or getattr(tk, "_default_root", None)


def show_info(title: str, message: str, *, parent=None, **_kwargs):
    """Theme-aware drop-in replacement for messagebox.showinfo."""
    resolved = _resolve_parent(parent)
    if resolved is None:
        return native_messagebox.showinfo(title, message, parent=parent)
    show_message(resolved, str(title), str(message), heading=str(title), kind="info")
    return "ok"


def show_warning(title: str, message: str, *, parent=None, **_kwargs):
    """Theme-aware drop-in replacement for messagebox.showwarning."""
    resolved = _resolve_parent(parent)
    if resolved is None:
        return native_messagebox.showwarning(title, message, parent=parent)
    show_message(resolved, str(title), str(message), heading=str(title), kind="warning")
    return "ok"


def show_error(title: str, message: str, *, parent=None, **_kwargs):
    """Theme-aware drop-in replacement for messagebox.showerror."""
    resolved = _resolve_parent(parent)
    if resolved is None:
        return native_messagebox.showerror(title, message, parent=parent)
    show_message(resolved, str(title), str(message), heading=str(title), kind="error")
    return "ok"


def ask_yes_no(title: str, message: str, *, parent=None, **_kwargs) -> bool:
    """Theme-aware drop-in replacement for messagebox.askyesno."""
    resolved = _resolve_parent(parent)
    if resolved is None:
        return bool(native_messagebox.askyesno(title, message, parent=parent))
    return ask_confirmation(
        resolved,
        str(title),
        str(message),
        heading=str(title),
        confirm_text=tr("Oui"),
        cancel_text=tr("Non"),
    )
