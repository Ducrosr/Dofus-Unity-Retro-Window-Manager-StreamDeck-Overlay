from __future__ import annotations

import unittest
import sys
from unittest.mock import Mock

from dwm.services.settings_search import SettingSearchEntry, find_settings
from dwm.ui_settings_search import SettingsSearch, navigate_to_setting


class SettingsSearchTests(unittest.TestCase):
    def setUp(self):
        self.entries = [
            SettingSearchEntry("Opacité", "Apparence / Overlay de rotation", "appearance", object()),
            SettingSearchEntry("Opacité", "Apparence / Notification", "appearance", object()),
            SettingSearchEntry("Fenêtre 1", "Raccourcis / Accès directs", "shortcuts", object()),
        ]

    def test_accents_case_and_word_order_are_ignored(self):
        self.assertEqual(find_settings(self.entries, "OVERLAY opacite"), self.entries[:1])
        self.assertEqual(find_settings(self.entries, "fenetre raccourcis"), self.entries[2:])

    def test_empty_and_missing_queries(self):
        for query in ("", "   ", "---", "inexistant", "overlay notification"):
            self.assertEqual(find_settings(self.entries, query), [])

    def test_all_tabs_and_partial_words_are_searched(self):
        self.assertEqual(len(find_settings(self.entries, "opac")), 2)
        self.assertEqual(find_settings(self.entries, "acces"), self.entries[2:])

    def test_direct_label_matches_rank_before_context_matches(self):
        entries = [SettingSearchEntry("Portraits", "Apparence / Overlay", "a", None),
                   SettingSearchEntry("Afficher l’overlay", "Apparence", "a", None)]
        self.assertEqual(find_settings(entries, "overlay"), list(reversed(entries)))

    def test_navigation_uses_content_coordinates_and_never_invokes_control(self):
        notebook, canvas, target = Mock(), Mock(), Mock()
        canvas.bbox.return_value = (0, 0, 500, 1000)
        canvas.winfo_rooty.return_value = 100
        target.winfo_rooty.return_value = 250
        canvas.canvasy.side_effect = lambda y: y + 100
        target.winfo_class.return_value = "TCheckbutton"
        entry = SettingSearchEntry("Test", "Appearance", "second", target)
        navigate_to_setting(notebook, {"second": canvas}, entry)
        notebook.select.assert_called_once_with("second")
        canvas.yview_moveto.assert_called_once_with(0.234)
        target.focus_set.assert_called_once()
        target.invoke.assert_not_called()

    def test_pending_search_is_cancelled_only_when_its_window_closes(self):
        search = SettingsSearch.__new__(SettingsSearch)
        search.win = Mock()
        search.pending = "callback"
        search.close(Mock(widget=object()))
        search.win.after_cancel.assert_not_called()
        search.close(Mock(widget=search.win))
        search.win.after_cancel.assert_called_once_with("callback")
        self.assertIsNone(search.pending)

    def test_actual_tk_search_navigates_without_changing_form(self):
        import tkinter as tk
        from tkinter import ttk
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            if sys.platform == "win32":
                raise
            self.skipTest(f"Graphical Tk unavailable: {exc}")
        try:
            root.withdraw()
            win = tk.Toplevel(root)
            win.geometry("650x600")
            notebook = ttk.Notebook(win)
            notebook.pack(fill="both", expand=True)
            first, second = ttk.Frame(notebook), ttk.Frame(notebook)
            notebook.add(first, text="Général")
            notebook.add(second, text="Apparence")
            canvas = tk.Canvas(second)
            canvas.pack(fill="both", expand=True)
            content = ttk.Frame(canvas)
            canvas.create_window((0, 0), window=content, anchor="nw")
            for index in range(35):
                ttk.Label(content, text=f"Option {index}").pack()
            value = tk.BooleanVar(master=win, value=False)
            ttk.Checkbutton(content, text="Opacité spéciale", variable=value).pack()
            win.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
            search = SettingsSearch(win, notebook, {str(second): canvas})
            search.query.set("opacite")
            search.open_first()
            win.update_idletasks()
            self.assertEqual(len(search.matches), 1)
            self.assertEqual(notebook.select(), str(second))
            self.assertGreater(canvas.yview()[0], 0)
            self.assertFalse(value.get())
            search.clear()
            search.open_first()
            win.update_idletasks()
            self.assertFalse(search.results_frame.winfo_manager())
            self.assertFalse(value.get())
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
