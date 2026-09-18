from __future__ import annotations

import hashlib
import os
import queue
import threading
import webbrowser
from pathlib import Path
from tkinter import StringVar, Toplevel, filedialog
from tkinter.ttk import Button, Frame, Label, Radiobutton

from .services.i18n import tr
from .ui_dialogs import ask_confirmation, show_message
from .ui_windowing import schedule_center_window
from .services.update_download import download_asset


class UpdateDownloadDialog:
    def __init__(self, root, release):
        self.window = Toplevel(root)
        self.window.title(tr("Mise à jour"))
        self.window.transient(root)
        schedule_center_window(self.window, root)
        self.cancel = threading.Event()
        self.events = queue.Queue()
        self.active = False
        self.asset = None
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        frame = Frame(self.window, padding=20)
        frame.pack(fill="both", expand=True)
        Label(
            frame,
            text=tr("Mise à jour disponible"),
            style="Header.TLabel",
        ).pack(anchor="w")
        Label(
            frame,
            text=tr("Nouvelle version : {tag}", tag=release.tag),
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(2, 16))
        self.choice = StringVar(value=release.assets[0].name)
        choices = Frame(frame)
        choices.pack(fill="x", pady=(0, 10))
        for asset in release.assets:
            Radiobutton(
                choices,
                text=asset.name,
                variable=self.choice,
                value=asset.name,
            ).pack(anchor="w", pady=2)
        self.status = StringVar(value=tr("Choisissez un fichier à télécharger et vérifier."))
        Label(
            frame,
            textvariable=self.status,
            wraplength=460,
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(4, 14))
        self.button = Button(
            frame,
            text=tr("Télécharger et vérifier"),
            command=lambda: self.start(release),
            style="Accent.TButton",
        )
        self.button.pack(fill="x")
        Button(
            frame,
            text=tr("Release officielle"),
            command=lambda: webbrowser.open(release.url),
        ).pack(fill="x", pady=(6, 0))
        Button(
            frame,
            text=tr("Annuler"),
            command=self.close,
            style="Quiet.TButton",
        ).pack(fill="x", pady=(6, 0))
        self.window.bind("<Destroy>", self._destroyed, add="+")

    def _destroyed(self, event):
        if event.widget == self.window:
            self.cancel.set()

    def close(self):
        self.cancel.set()
        if self.active:
            self.status.set(tr("Annulation en cours…"))
        else:
            self.window.destroy()

    def start(self, release):
        directory = filedialog.askdirectory(parent=self.window, title=tr("Dossier de téléchargement"))
        if not directory:
            return
        self.cancel.clear()
        self.asset = next(a for a in release.assets if a.name == self.choice.get())
        self.active = True
        self.button.state(["disabled"])
        self.status.set(tr("Téléchargement en cours…"))

        def worker():
            last = -1

            def progress(count, total):
                nonlocal last
                percent = count * 100 // total
                if percent != last:
                    last = percent
                    self.events.put(("progress", percent))
            try:
                path = download_asset(self.asset, Path(directory), self.cancel, progress)
                self.events.put(("done", path))
            except InterruptedError:
                self.events.put(("error", "Téléchargement annulé."))
            except Exception:
                self.events.put(("error", "Téléchargement ou vérification impossible. Aucun fichier ne sera lancé."))

        threading.Thread(target=worker, name="DWMUpdateDownload", daemon=True).start()
        self.window.after(100, self.poll)

    def poll(self):
        while not self.events.empty():
            kind, value = self.events.get_nowait()
            if kind == "progress":
                self.status.set(tr("Téléchargement : {percent} %", percent=value))
                continue
            self.active = False
            self.button.state(["!disabled"])
            if kind == "error":
                self.status.set(tr(value))
            else:
                self.finish(value)
                return
        if self.active:
            self.window.after(100, self.poll)

    def finish(self, path):
        self.status.set(tr("SHA-256 vérifié."))
        self.button.state(["disabled"])
        if self.cancel.is_set():
            self.window.destroy()
            return
        if self.asset.name == "DofusWindowManager-Setup.exe":
            if ask_confirmation(
                self.window,
                tr("Mise à jour"),
                tr("SHA-256 vérifié. Lancer l’installateur ?") + "\n\n" + str(path),
                confirm_text=tr("Lancer l’installateur"),
                cancel_text=tr("Annuler"),
            ):
                try:
                    with path.open("rb") as downloaded:
                        if hashlib.file_digest(downloaded, "sha256").hexdigest() != self.asset.sha256:
                            raise ValueError("SHA-256")
                    os.startfile(str(path))
                except Exception:
                    show_message(
                        self.window,
                        tr("Mise à jour"),
                        tr("Impossible de lancer le fichier vérifié."),
                        heading=tr("Ouverture impossible"),
                    )
        else:
            show_message(
                self.window,
                tr("Mise à jour"),
                tr("Fermez l’application avant de remplacer votre EXE portable.")
                + "\n\n"
                + str(path),
                heading=tr("Fichier vérifié"),
            )
