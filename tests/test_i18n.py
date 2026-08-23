from __future__ import annotations

import unittest

from dwm.services.i18n import normalize_language, set_language, tr, translation_source


class I18nTests(unittest.TestCase):
    def tearDown(self) -> None:
        set_language("fr")

    def test_french_is_the_default_and_fallback(self) -> None:
        self.assertEqual(normalize_language("de"), "fr")
        self.assertEqual(tr("Paramètres", language="fr"), "Paramètres")

    def test_english_and_spanish_catalogs(self) -> None:
        self.assertEqual(tr("Paramètres", language="en"), "Settings")
        self.assertEqual(tr("Paramètres", language="es"), "Ajustes")
        self.assertEqual(
            tr("Mode {game} · gestion locale des fenêtres", language="en", game="Unity"),
            "Unity mode · local window management",
        )
        self.assertEqual(tr("Demandes d’attention", language="en"), "Attention requests")
        self.assertEqual(tr("Réinitialiser l’affichage…", language="es"), "Restablecer visualización…")
        self.assertEqual(tr("Dépôt GitHub officiel", language="en"), "Official GitHub repository")
        self.assertEqual(tr("Conseils anti-phishing Ankama", language="es"), "Consejos anti-phishing de Ankama")

    def test_translated_text_can_be_mapped_back_to_its_source(self) -> None:
        self.assertEqual(translation_source("Settings"), "Paramètres")
        self.assertEqual(translation_source("Ajustes"), "Paramètres")
        self.assertIsNone(translation_source("Nealla"))
