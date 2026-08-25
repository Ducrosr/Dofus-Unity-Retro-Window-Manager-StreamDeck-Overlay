from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InstallerDefinitionTests(unittest.TestCase):
    def test_inno_setup_is_per_user_and_packages_only_the_built_executable(self) -> None:
        definition = (ROOT / "installer" / "DofusWindowManager.iss").read_text(encoding="utf-8")
        self.assertIn("PrivilegesRequired=lowest", definition)
        self.assertIn("{localappdata}\\Programs\\DofusWindowManager", definition)
        self.assertIn('Source: "..\\release-assets\\{#AppExeName}"', definition)
        self.assertNotIn("Password", definition)

    def test_release_workflow_builds_hashes_and_conditionally_signs_both_windows_files(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        signing_script = (ROOT / "installer" / "sign_windows.ps1").read_text(encoding="utf-8")
        self.assertIn("DofusWindowManager-Setup.exe.sha256", workflow)
        self.assertIn("WINDOWS_SIGNING_CERTIFICATE_BASE64", workflow)
        self.assertIn("dist/DofusWindowManager.exe", workflow)
        self.assertIn("release-assets/DofusWindowManager-Setup.exe", workflow)
        self.assertIn("signtool.exe", signing_script)
        self.assertNotIn("BEGIN CERTIFICATE", signing_script)

