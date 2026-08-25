from __future__ import annotations

import argparse

from dwm.utils.paths import ensure_dirs
from dwm.utils.logging import AppLogger, install_excepthook
from dwm.services.app_launcher import register_current_launcher
from dwm.services.windows_startup import set_startup_enabled
from dwm.storage.settings import load_settings, save_settings


def should_prompt_for_game_mode(settings, *, use_saved_mode: bool) -> bool:
    """Keep the legacy mode picker except while the guided setup is pending."""
    return not bool(use_saved_mode) and bool(settings.onboarding_completed)


def choose_game_dialog(default_mode: str = "unity", language: str = "fr") -> tuple[str, bool]:
    """Small startup dialog to pick Unity vs Retro.

    Returns: (game_mode, remember_choice)
    """
    import tkinter as tk
    from tkinter import ttk
    from dwm.services.i18n import set_language, tr

    set_language(language)

    gm = (default_mode or "unity").strip().lower()
    if gm not in ("unity", "retro"):
        gm = "unity"

    result = {"mode": gm, "remember": True, "ok": False}

    root = tk.Tk()
    root.title(tr("Choisir le jeu"))
    root.resizable(False, False)

    # Center-ish
    try:
        root.update_idletasks()
        w, h = 360, 170
        x = (root.winfo_screenwidth() // 2) - (w // 2)
        y = (root.winfo_screenheight() // 2) - (h // 2)
        root.geometry(f"{w}x{h}+{x}+{y}")
    except Exception:
        pass

    mode_var = tk.StringVar(value=gm)
    remember_var = tk.BooleanVar(value=True)

    frm = ttk.Frame(root, padding=12)
    frm.pack(fill="both", expand=True)

    ttk.Label(frm, text=tr("Sélectionne la version de Dofus :"), font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 8))

    ttk.Radiobutton(frm, text="Dofus Unity", value="unity", variable=mode_var).pack(anchor="w")
    ttk.Radiobutton(frm, text="Dofus Retro", value="retro", variable=mode_var).pack(anchor="w", pady=(0, 6))

    ttk.Checkbutton(frm, text=tr("Mémoriser ce choix (pré-sélection au prochain lancement)"), variable=remember_var).pack(anchor="w", pady=(6, 10))

    btns = ttk.Frame(frm)
    btns.pack(fill="x")

    def on_ok():
        result["mode"] = mode_var.get().strip().lower() or "unity"
        result["remember"] = bool(remember_var.get())
        result["ok"] = True
        root.destroy()

    def on_cancel():
        root.destroy()

    ttk.Button(btns, text="OK", command=on_ok).pack(side="right")
    ttk.Button(btns, text=tr("Annuler"), command=on_cancel).pack(side="right", padx=(0, 8))

    root.bind("<Return>", lambda e: on_ok())
    root.bind("<Escape>", lambda e: on_cancel())

    root.mainloop()

    if not result["ok"]:
        # If cancelled/closed, keep default
        return gm, False
    return result["mode"], result["remember"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Dofus Window Manager")
    parser.add_argument("--minimized", action="store_true", help="démarre dans la zone de notification")
    parser.add_argument(
        "--use-saved-mode",
        action="store_true",
        help="utilise directement le mode Unity/Retro mémorisé",
    )
    args = parser.parse_args()

    dirs = ensure_dirs()
    logger = AppLogger(
        log_file=dirs["logs"] / "app.log",
        actions_file=dirs["logs"] / "actions.log",
    )
    install_excepthook(logger)

    try:
        register_current_launcher(dirs["root"])
    except OSError as exc:
        logger.warn(f"Impossible d'enregistrer le lanceur Stream Deck : {exc}")

    settings_path = dirs["root"] / "settings.json"
    settings = load_settings(settings_path)

    if settings.start_with_windows:
        try:
            set_startup_enabled(True)
        except OSError as exc:
            logger.warn(f"Impossible d’actualiser le démarrage Windows : {exc}")

    if should_prompt_for_game_mode(settings, use_saved_mode=args.use_saved_mode):
        mode, remember = choose_game_dialog(settings.game_mode, settings.language)
        if remember:
            settings.game_mode = mode
            save_settings(settings_path, settings)
    else:
        mode = settings.game_mode

    from dwm.app import run

    run(game_mode=mode, start_minimized=args.minimized)


if __name__ == "__main__":
    main()
