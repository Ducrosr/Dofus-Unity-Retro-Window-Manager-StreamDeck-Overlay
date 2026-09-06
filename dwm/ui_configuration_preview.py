from __future__ import annotations

import json
from tkinter import TclError, Text, Toplevel
from tkinter.ttk import Button, Frame, Label, Scrollbar, Style, Treeview

from .services.configuration_diff import ConfigurationChange
from .services.i18n import tr


FIELD_LABELS = {
    "theme": "Thème", "language": "Langue", "game_mode": "Version de Dofus",
    "order": "Ordre", "aliases": "Alias", "visuals": "Apparences", "name": "Nom",
    "character_slots": "Emplacements", "ignored_characters": "Personnages ignorés",
    "active_profile": "Profil actif", "last_profile": "Dernier profil",
    "hotkeys": "Raccourcis", "hotkey_scope": "Portée des raccourcis",
    "fixed_character_slots": "Emplacements fixes", "start_with_windows": "Démarrage Windows",
    "overlay_by_game_mode": "Disposition d’overlay", "display_by_game_mode": "Affichage par mode",
    "theme_by_game_mode": "Thème par mode", "rotation_overlay_enabled": "Afficher l’overlay",
    "rotation_overlay_x": "Position horizontale", "rotation_overlay_y": "Position verticale",
    "rotation_overlay_width": "Largeur", "rotation_overlay_height": "Hauteur",
    "rotation_overlay_auto_width": "Largeur automatique", "rotation_overlay_opacity": "Opacité",
    "rotation_overlay_orientation": "Orientation", "rotation_overlay_locked": "Verrouillage",
    "rotation_overlay_layout": "Contenu de l’overlay", "rotation_overlay_show_title": "Titre de l’overlay",
    "rotation_overlay_show_reorder_buttons": "Flèches de réorganisation",
    "show_overlay_portraits": "Portraits de l’overlay", "show_overlay_badges": "Icônes de l’overlay",
    "portrait": "Portrait", "badge": "Icône", "auto_refresh": "Actualisation automatique",
    "refresh_seconds": "Intervalle d’actualisation", "smart_profile_loading_enabled": "Chargement intelligent des profils",
    "security_notice_accepted": "Avertissement de sécurité accepté", "onboarding_completed": "Assistant terminé",
    "window_column_order": "Ordre des colonnes", "minimize_to_tray": "Réduction dans la zone de notification",
    "check_updates_automatically": "Recherche automatique des mises à jour", "include_prereleases": "Inclure les préversions",
    "last_update_check_at": "Dernière recherche de mise à jour", "compact_window_geometry": "Position et taille du mode compact",
    "swap_notification_enabled": "Notification de changement de fenêtre", "swap_notification_anchor": "Position de la notification",
    "swap_notification_duration_ms": "Durée de la notification (ms)", "swap_notification_opacity": "Opacité de la notification",
    "swap_notification_layout": "Contenu de la notification", "attention_blink_enabled": "Clignotement des alertes",
    "show_popup_portraits": "Portraits des notifications", "show_popup_badges": "Icônes des notifications",
    "show_character_portraits": "Portraits des personnages", "show_character_badges": "Icônes des personnages",
    "character_visuals": "Apparences des personnages", "accessibility_high_contrast": "Contraste renforcé",
    "accessibility_reduce_motion": "Réduction des animations", "accessibility_ui_scale_percent": "Échelle de l’interface (%)",
    "adaptive_performance_enabled": "Performances adaptatives", "event_hook_enabled": "Synchronisation Windows",
    "popup_watch_enabled": "Détection des alertes Retro", "retro_title_keyword": "Filtre de titre Retro",
    "retro_process_keyword": "Filtre de processus Retro",
}


def readable_path(change: ConfigurationChange) -> str:
    parts = [tr(change.section)]
    for position, part in enumerate(change.path):
        is_name = (change.section == "Profils" and position == 0) or (
            position > 0 and change.path[position - 1] in {"aliases", "visuals", "character_visuals"}
        )
        parts.append(part if is_name else tr(FIELD_LABELS.get(part, part.replace("_", " "))))
    return " / ".join(parts)


def readable_value(value: object) -> str:
    def clean(item):
        if isinstance(item, str) and item.startswith("data:image/"):
            return tr("Image personnalisée")
        if isinstance(item, dict):
            return {key: clean(value) for key, value in item.items()}
        if isinstance(item, list):
            return [clean(value) for value in item]
        return item
    value = clean(value)
    if value is None:
        return "—"
    if isinstance(value, bool):
        return tr("Oui") if value else tr("Non")
    if isinstance(value, str):
        return value or tr("Vide")
    return json.dumps(value, ensure_ascii=False, indent=2)


def confirm_configuration_changes(parent, changes: list[ConfigurationChange], retained: int) -> bool:
    previous_grab = parent.grab_current()
    win = Toplevel(parent)
    win.title(tr("Aperçu des modifications"))
    win.transient(parent)
    win.geometry(f"{min(1000, max(520, win.winfo_screenwidth() - 100))}x{min(680, max(400, win.winfo_screenheight() - 120))}")
    win.minsize(520, 400)
    content = Frame(win, padding=12)
    content.pack(fill="both", expand=True)
    Label(content, text=tr("{count} différence(s) ; {retained} profil(s) local(aux) conservé(s).",
                           count=len(changes), retained=retained)).pack(anchor="w")
    Label(content, text=tr("Un point de restauration sera créé après validation."), wraplength=650).pack(anchor="w", pady=(4, 8))
    table_frame = Frame(content)
    table_frame.pack(fill="both", expand=True)
    table = Treeview(table_frame, columns=("field", "before", "after"), show="headings", selectmode="browse", height=6)
    for key, label, width in (("field", "Élément", 320), ("before", "Avant", 230), ("after", "Après", 230)):
        table.heading(key, text=tr(label))
        table.column(key, width=width, minwidth=80)
    scroll = Scrollbar(table_frame, command=table.yview)
    table.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    table.pack(fill="both", expand=True)
    detail_frame = Frame(content)
    detail_frame.pack(fill="both", pady=(8, 8))
    details = Text(detail_frame, height=7, wrap="word", state="disabled")
    style = Style(win)
    details.configure(background=style.lookup("TLabel", "background") or "white",
                      foreground=style.lookup("TLabel", "foreground") or "black")
    detail_scroll = Scrollbar(detail_frame, command=details.yview)
    details.configure(yscrollcommand=detail_scroll.set)
    detail_scroll.pack(side="right", fill="y")
    details.pack(fill="both", expand=True)
    formatted = []
    for index, change in enumerate(changes):
        label = readable_path(change)
        before, after = readable_value(change.before), readable_value(change.after)
        formatted.append((label, before, after))
        table.insert("", "end", iid=str(index), values=(label, before.replace("\n", " ")[:200], after.replace("\n", " ")[:200]))

    def show_details(_event=None):
        selection = table.selection()
        if not selection:
            return
        label, before, after = formatted[int(selection[0])]
        details.configure(state="normal")
        details.delete("1.0", "end")
        details.insert("1.0", f"{label}\n\n{tr('Avant')} :\n{before}\n\n{tr('Après')} :\n{after}")
        details.configure(state="disabled")

    table.bind("<<TreeviewSelect>>", show_details)
    if changes:
        table.selection_set("0")
        show_details()
    else:
        Label(content, text=tr("Aucune modification à appliquer.")).pack(anchor="w")
    accepted = False

    def accept():
        nonlocal accepted
        accepted = True
        win.destroy()

    footer = Frame(content)
    footer.pack(fill="x")
    Button(footer, text=tr("Annuler"), command=win.destroy).pack(side="right")
    Button(footer, text=tr("Appliquer les modifications"), command=accept,
           state="normal" if changes else "disabled").pack(side="right", padx=8)
    win.bind("<Escape>", lambda _event: win.destroy())
    win.grab_set()
    try:
        parent.wait_window(win)
    finally:
        try:
            if previous_grab is not None and previous_grab.winfo_exists():
                previous_grab.grab_set()
        except TclError:
            pass  # The application may have been closed while the preview was open.
    return accepted
