from __future__ import annotations

from tkinter import StringVar, TclError
from tkinter.ttk import Button, Entry, Frame, Label, Scrollbar, Treeview

from .services.i18n import tr
from .services.settings_search import SettingSearchEntry, find_settings


def collect_settings_entries(notebook, tab_canvases) -> list[SettingSearchEntry]:
    entries = []
    for tab in notebook.tabs():
        canvas = tab_canvases.get(str(tab))
        if canvas is None:
            continue
        tab_label = str(notebook.tab(tab, "text"))

        def visit(widget, context, tab_id=str(tab)):
            kind = widget.winfo_class()
            text = str(widget.cget("text")) if "text" in widget.keys() else ""
            if kind == "TLabelframe" and text:
                context = f"{context} / {text}"
            elif kind in {"TLabel", "TCheckbutton", "TRadiobutton"} and text.strip():
                entries.append(SettingSearchEntry(text.strip(), context, tab_id, widget))
            for child in widget.winfo_children():
                visit(child, context)

        visit(canvas, tab_label)
    return entries


def navigate_to_setting(notebook, tab_canvases, entry: SettingSearchEntry) -> None:
    notebook.select(entry.tab)
    notebook.update_idletasks()
    canvas = tab_canvases[entry.tab]
    bounds = canvas.bbox("all")
    if bounds is None:
        return
    target = entry.target
    # Convert viewport coordinates back to content coordinates even after scrolling.
    y = canvas.canvasy(target.winfo_rooty() - canvas.winfo_rooty())
    height = max(1, bounds[3] - bounds[1])
    canvas.yview_moveto(max(0.0, min(1.0, (y - bounds[1] - 16) / height)))
    if target.winfo_class() in {"TCheckbutton", "TRadiobutton"}:
        target.focus_set()


class SettingsSearch:
    def __init__(self, win, notebook, tab_canvases):
        self.win = win
        self.notebook = notebook
        self.tab_canvases = tab_canvases
        self.entries = collect_settings_entries(notebook, tab_canvases)
        self.matches = []
        self.pending = None
        self.query = StringVar(master=win)
        self.status = StringVar(master=win)
        self.frame = Frame(win, padding=(12, 8, 12, 0))
        self.frame.pack(fill="x", before=notebook)
        row = Frame(self.frame)
        row.pack(fill="x")
        Label(row, text=tr("Rechercher un paramètre")).pack(side="left", padx=(0, 8))
        self.entry = Entry(row, textvariable=self.query)
        self.entry.pack(side="left", fill="x", expand=True)
        Button(row, text=tr("Effacer"), command=lambda: self.query.set("")).pack(side="right", padx=(8, 0))
        self.results_frame = Frame(self.frame)
        Label(self.results_frame, textvariable=self.status).pack(anchor="w", pady=3)
        table_frame = Frame(self.results_frame)
        table_frame.pack(fill="x")
        self.table = Treeview(table_frame, columns=("context", "label"), show="headings", height=4, selectmode="browse")
        self.table.heading("context", text=tr("Emplacement"))
        self.table.heading("label", text=tr("Paramètre"))
        self.table.column("context", width=200, minwidth=80)
        self.table.column("label", width=370, minwidth=120)
        scrollbar = Scrollbar(table_frame, command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.table.pack(fill="x")
        self.table.bind("<<TreeviewSelect>>", self.open_selected)
        self.table.bind("<MouseWheel>", self.scroll_results)
        self.entry.bind("<Return>", self.open_first)
        self.entry.bind("<Escape>", self.clear)
        win.bind("<Control-f>", self.focus, add="+")
        win.bind("<Destroy>", self.close, add="+")
        self.query.trace_add("write", self.schedule)

    def focus(self, _event=None):
        self.entry.focus_set()
        self.entry.selection_range(0, "end")
        return "break"

    def clear(self, _event=None):
        self.query.set("")
        return "break"

    def schedule(self, *_args):
        if self.pending is not None:
            self.win.after_cancel(self.pending)
        self.pending = self.win.after(120, self.render)

    def render(self):
        self.pending = None
        # Labels can change after the initial window construction (localization).
        self.entries = collect_settings_entries(self.notebook, self.tab_canvases)
        self.matches = find_settings(self.entries, self.query.get())
        self.table.delete(*self.table.get_children())
        if not self.query.get().strip():
            self.results_frame.pack_forget()
            return
        self.results_frame.pack(fill="x", pady=(2, 0))
        self.status.set(tr("{count} résultat(s)", count=len(self.matches)) if self.matches else tr("Aucun paramètre trouvé."))
        for index, entry in enumerate(self.matches):
            self.table.insert("", "end", iid=str(index), values=(entry.context, entry.label))

    def open_first(self, _event=None):
        if self.pending is not None:
            self.win.after_cancel(self.pending)
            self.render()
        if self.matches:
            self.table.selection_set("0")
            self.open_selected()
        return "break"

    def open_selected(self, _event=None):
        selection = self.table.selection()
        if selection:
            index = int(selection[0])
            if index < len(self.matches):
                navigate_to_setting(self.notebook, self.tab_canvases, self.matches[index])

    def scroll_results(self, event):
        from .services.ui_scroll import wheel_scroll_units
        self.table.yview_scroll(wheel_scroll_units(event.delta), "units")
        return "break"

    def close(self, event):
        if event.widget is self.win and self.pending is not None:
            try:
                self.win.after_cancel(self.pending)
            except TclError:
                pass
            self.pending = None
