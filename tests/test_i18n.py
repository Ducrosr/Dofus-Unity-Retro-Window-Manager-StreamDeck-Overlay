from __future__ import annotations

import unittest
from pathlib import Path

from PIL import Image

from dwm.services.i18n import normalize_language, set_language, tr, translation_source


class I18nTests(unittest.TestCase):
    def test_language_flag_assets_are_packaged_and_readable(self) -> None:
        flags_dir = Path(__file__).resolve().parents[1] / "assets" / "flags"
        for language in ("fr", "en", "es"):
            with Image.open(flags_dir / f"{language}.png") as flag:
                self.assertGreaterEqual(flag.width, 90)
                self.assertEqual(flag.height, 60)

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
        self.assertEqual(tr("Apparence", language="en"), "Appearance")
        self.assertEqual(tr("Raccourcis", language="es"), "Atajos")
        self.assertEqual(tr("Avertissement de sécurité", language="en"), "Security warning")
        self.assertEqual(tr("Continuer", language="es"), "Continuar")
        self.assertEqual(
            tr("Assistant de configuration…", language="en"),
            "Setup assistant…",
        )
        self.assertEqual(
            tr("Fenêtres détectées : {count}", language="es", count=8),
            "Ventanas detectadas: 8",
        )
        self.assertEqual(
            tr("Afficher le titre de l’overlay", language="en"),
            "Show the overlay title",
        )
        self.assertEqual(
            tr("Afficher les flèches de réorganisation", language="es"),
            "Mostrar las flechas de reordenación",
        )
        self.assertEqual(
            tr("Adapter automatiquement la largeur de l’overlay au contenu", language="en"),
            "Automatically fit the overlay width to its content",
        )
        self.assertEqual(
            tr("Afficher les icônes dans la notification", language="es"),
            "Mostrar iconos en la notificación",
        )
        self.assertEqual(
            tr("Aperçu Stream Deck multi-modèles", language="en"),
            "Multi-device Stream Deck preview",
        )
        self.assertEqual(
            tr("Modèle de Stream Deck", language="es"),
            "Modelo de Stream Deck",
        )
        self.assertEqual(
            tr("Charger automatiquement un profil reconnu exactement", language="en"),
            "Automatically load an exact recognized profile",
        )
        self.assertEqual(
            tr(
                "Espacer les scans de contrôle lorsque la détection en temps réel est active",
                language="es",
            ),
            "Espaciar los escaneos de control cuando la detección en tiempo real esté activa",
        )
        self.assertEqual(
            tr("Créer un paquet de support…", language="en"),
            "Create a support bundle…",
        )
        self.assertEqual(tr("Préréglages d’affichage", language="es"), "Preajustes de visualización")
        self.assertEqual(tr("Équilibré", language="en"), "Balanced")
        self.assertEqual(tr("Capturer un raccourci", language="en"), "Capture a shortcut")
        self.assertEqual(tr("Points de restauration locaux", language="en"), "Local restore points")
        self.assertEqual(tr("Contraste renforcé", language="es"), "Contraste alto")
        self.assertEqual(
            tr("Installer ou réparer le plugin Stream Deck", language="en"),
            "Install or repair the Stream Deck plugin",
        )

    def test_translated_text_can_be_mapped_back_to_its_source(self) -> None:
        self.assertEqual(translation_source("Settings"), "Paramètres")
        self.assertEqual(translation_source("Ajustes"), "Paramètres")
        self.assertIsNone(translation_source("Nealla"))
