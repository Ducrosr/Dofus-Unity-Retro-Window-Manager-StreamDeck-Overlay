from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from dwm.services.i18n import set_language
from dwm.ui_dialogs import _run_modal, ask_yes_no, show_error, show_info, show_warning


class ThemedDialogAdapterTests(unittest.TestCase):
    def tearDown(self) -> None:
        set_language("fr")

    def test_information_variants_use_dwm_modal_surface(self):
        parent = object()
        cases = (
            (show_info, "info"),
            (show_warning, "warning"),
            (show_error, "error"),
        )

        for helper, kind in cases:
            with self.subTest(kind=kind), patch("dwm.ui_dialogs.show_message") as modal:
                result = helper("Titre", "Message", parent=parent)

            self.assertEqual(result, "ok")
            modal.assert_called_once_with(
                parent,
                "Titre",
                "Message",
                heading="Titre",
                kind=kind,
            )

    def test_nested_modal_restores_previous_grab(self):
        parent = Mock()
        previous = Mock()
        previous.winfo_exists.return_value = 1
        parent.grab_current.return_value = previous
        win = Mock()

        _run_modal(win, parent)

        win.grab_set.assert_called_once()
        parent.wait_window.assert_called_once_with(win)
        previous.grab_set.assert_called_once()

    def test_yes_no_uses_themed_confirmation_and_current_language(self):
        parent = object()
        set_language("en")

        with patch("dwm.ui_dialogs.ask_confirmation", return_value=True) as modal:
            accepted = ask_yes_no("Question", "Continue?", parent=parent)

        self.assertTrue(accepted)
        modal.assert_called_once_with(
            parent,
            "Question",
            "Continue?",
            heading="Question",
            confirm_text="Yes",
            cancel_text="No",
        )


if __name__ == "__main__":
    unittest.main()
