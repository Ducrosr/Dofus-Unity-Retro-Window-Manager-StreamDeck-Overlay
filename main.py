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


def choose_game_dialog(
    default_mode: str = "unity",
    language: str = "fr",
    theme_name: str = "unity-standard",
) -> tuple[str, bool]:
    """Small startup dialog to pick Unity vs Retro.

    Returns: (game_mode, remember_choice)
    """
    import tkinter as tk
    from tkinter import ttk
    from dwm.services.i18n import set_language, tr
    from dwm.services.themes import normalize_theme, theme_palette
    from dwm.ui_windowing import apply_windows_dark_titlebar, center_window_on_parent

    set_language(language)

    gm = (default_mode or "unity").strip().lower()
    if gm not in ("unity", "retro"):
        gm = "unity"

    result = {"mode": gm, "remember": True, "ok": False}

    root = tk.Tk()
    root.title(tr("Choisir le jeu"))
    root.resizable(False, False)
    root.geometry("520x300")

    palette = theme_palette(normalize_theme(theme_name, gm))
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    root.configure(background=palette["bg"])
    style.configure(
        ".",
        background=palette["bg"],
        foreground=palette["fg"],
        fieldbackground=palette["bg2"],
        bordercolor=palette["line"],
        font=("Segoe UI", 10),
    )
    style.configure("TFrame", background=palette["bg"])
    style.configure("TLabel", background=palette["bg"], foreground=palette["fg"])
    style.configure(
        "StartupHeader.TLabel",
        background=palette["bg"],
        foreground=palette["accent"],
        font=("Segoe UI", 18, "bold"),
    )
    style.configure(
        "StartupMuted.TLabel",
        background=palette["bg"],
        foreground=palette["muted"],
    )
    style.configure(
        "TButton",
        background=palette["bg3"],
        foreground=palette["on_dark"],
        borderwidth=0,
        padding=(12, 8),
    )
    style.configure(
        "StartupAccent.TButton",
        background=palette["accent"],
        foreground=palette["on_accent"],
        borderwidth=0,
        padding=(13, 8),
        font=("Segoe UI", 10, "bold"),
    )
    style.map(
        "StartupAccent.TButton",
        background=[
            ("active", palette["accent_hover"]),
            ("pressed", palette["accent_pressed"]),
        ],
    )
    style.configure("TRadiobutton", background=palette["bg"], foreground=palette["fg"])
    style.configure("TCheckbutton", background=palette["bg"], foreground=palette["fg"])

    root.update_idletasks()
    center_window_on_parent(root, None)
    root.after_idle(lambda: apply_windows_dark_titlebar(root))

    mode_var = tk.StringVar(value=gm)
    remember_var = tk.BooleanVar(value=True)

    frm = ttk.Frame(root, padding=22)
    frm.pack(fill="both", expand=True)

    ttk.Label(
        frm,
        text=tr("Choisir la version de Dofus"),
        style="StartupHeader.TLabel",
    ).pack(anchor="w")
    ttk.Label(
        frm,
        text=tr("Sélectionnez la version que DWM doit gérer pour cette session."),
        style="StartupMuted.TLabel",
    ).pack(anchor="w", pady=(4, 18))

    choices = ttk.Frame(frm)
    choices.pack(fill="x")
    ttk.Radiobutton(
        choices,
        text="Dofus Unity",
        value="unity",
        variable=mode_var,
    ).pack(anchor="w", pady=3)
    ttk.Radiobutton(
        choices,
        text="Dofus Retro",
        value="retro",
        variable=mode_var,
    ).pack(anchor="w", pady=3)

    ttk.Checkbutton(
        frm,
        text=tr("Mémoriser ce choix (pré-sélection au prochain lancement)"),
        variable=remember_var,
    ).pack(anchor="w", pady=(16, 18))

    btns = ttk.Frame(frm)
    btns.pack(fill="x")

    def on_ok():
        result["mode"] = mode_var.get().strip().lower() or "unity"
        result["remember"] = bool(remember_var.get())
        result["ok"] = True
        root.destroy()

    def on_cancel():
        root.destroy()

    ttk.Button(
        btns,
        text=tr("Continuer"),
        command=on_ok,
        style="StartupAccent.TButton",
    ).pack(side="right")
    ttk.Button(
        btns,
        text=tr("Annuler"),
        command=on_cancel,
    ).pack(side="right", padx=(0, 8))

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
        mode, remember = choose_game_dialog(
            settings.game_mode,
            settings.language,
            settings.theme,
        )
        if remember:
            settings.game_mode = mode
            save_settings(settings_path, settings)
    else:
        mode = settings.game_mode

    from dwm.services.session_recovery import SessionRecovery
    from dwm.services.obs_overlay_capture import enable_obs_overlay_capture

    recovery = SessionRecovery(dirs["root"])
    try:
        recovery.begin()
    except OSError as exc:
        logger.warn(f"Session recovery unavailable: {exc}")
    try:
        enable_obs_overlay_capture()
        from dwm.app import run

        run(game_mode=mode, start_minimized=args.minimized,
            previous_interruption=recovery.previous_interruption)
        try:
            recovery.complete()
        except OSError as exc:
            logger.warn(f"Session completion could not be recorded: {exc}")
    finally:
        recovery.close()


if __name__ == "__main__":
    main()
