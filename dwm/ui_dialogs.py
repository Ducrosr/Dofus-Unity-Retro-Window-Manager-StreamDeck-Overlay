from __future__ import annotations

from tkinter import StringVar, Toplevel
from tkinter.ttk import Button, Entry, Frame, Label

from .ui_windowing import schedule_center_window


def _prepare_dialog(parent, title: str) -> tuple[Toplevel, Frame]:
    win = Toplevel(parent)
    win.title(title)
    win.transient(parent)
    win.resizable(False, False)

    body = Frame(win, padding=20)
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


def show_message(
    parent,
    title: str,
    message: str,
    *,
    heading: str | None = None,
    button_text: str = "OK",
) -> None:
    win, body = _prepare_dialog(parent, title)
    Label(
        body,
        text=heading or title,
        style="Header.TLabel",
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
        style="Accent.TButton",
    ).pack(side="right")

    win.bind("<Return>", lambda _event: win.destroy())
    win.bind("<Escape>", lambda _event: win.destroy())
    _finish_dialog_layout(win, parent, 500)
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
        style="Danger.TButton" if danger else "Accent.TButton",
    ).pack(side="right")
    Button(
        footer,
        text=cancel_text,
        command=win.destroy,
        style="Quiet.TButton",
    ).pack(side="right", padx=(0, 8))

    win.bind("<Return>", lambda _event: accept())
    win.bind("<Escape>", lambda _event: win.destroy())
    _finish_dialog_layout(win, parent, 520)
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
        if not candidate:
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
        style="Accent.TButton",
    ).pack(side="right")
    Button(
        footer,
        text=cancel_text,
        command=win.destroy,
        style="Quiet.TButton",
    ).pack(side="right", padx=(0, 8))

    win.bind("<Return>", lambda _event: accept())
    win.bind("<Escape>", lambda _event: win.destroy())
    try:
        entry.selection_range(0, "end")
        entry.focus_set()
    except Exception:
        pass
    _finish_dialog_layout(win, parent, 500)
    _run_modal(win, parent)
    return result["value"]
