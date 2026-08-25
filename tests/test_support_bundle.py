from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from dwm.services.support_bundle import create_support_bundle, redact_support_text


class SupportBundleTests(unittest.TestCase):
    def test_redaction_removes_known_values_paths_ids_and_email(self) -> None:
        text = (
            "Nealla alias Terre hwnd=12345 C:\\Users\\Remy\\AppData "
            "remy@example.com /home/remy/project"
        )
        redacted = redact_support_text(
            text,
            sensitive_values=["Nealla", "Terre"],
            private_paths=["/home/remy/project"],
            window_ids=[12345],
        )

        for secret in ("Nealla", "Terre", "12345", "Remy", "remy@example.com"):
            self.assertNotIn(secret.casefold(), redacted.casefold())
        self.assertIn("<ID_FENETRE>", redacted)
        self.assertIn("<EMAIL>", redacted)

    def test_bundle_contains_only_sanitized_settings_and_redacted_log_tails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_path = root / "app.log"
            log_path.write_text(
                "Focus Nealla (98765) profil Jiva alias Terre\n",
                encoding="utf-8",
            )
            bundle = root / "support.zip"
            create_support_bundle(
                bundle,
                diagnostic_report=f"Profil actif: Jiva\nDossier: {root}\n",
                settings={
                    "last_profile": "Jiva",
                    "character_visuals": {
                        "Nealla": {"portrait": "data:image/png;base64,SECRET", "badge": "force"}
                    },
                    "theme": "standard",
                },
                log_paths=[log_path],
                sensitive_values=["Nealla", "Jiva", "Terre"],
                private_paths=[root],
                window_ids=[98765],
                app_version="2.20.0",
            )

            with zipfile.ZipFile(bundle) as archive:
                names = set(archive.namelist())
                combined = "\n".join(
                    archive.read(name).decode("utf-8") for name in names
                )
                settings = json.loads(archive.read("settings-sanitized.json"))

        self.assertEqual(
            names,
            {"README.txt", "manifest.json", "diagnostic.txt", "settings-sanitized.json", "logs/app.log"},
        )
        for secret in ("Nealla", "Jiva", "Terre", "98765", "SECRET", str(root)):
            self.assertNotIn(secret.casefold(), combined.casefold())
        self.assertEqual(settings["last_profile"], "<PROFIL_PRIVE>")
        self.assertEqual(settings["character_visuals"], {"entries_removed": 1})

