from __future__ import annotations

import unittest

from dwm.services.streamdeck_health import evaluate_streamdeck_plugin_health


class StreamDeckHealthTests(unittest.TestCase):
    def test_missing_or_outdated_plugin_recommends_repair(self) -> None:
        missing = evaluate_streamdeck_plugin_health(None, "0.8.0.0")
        outdated = evaluate_streamdeck_plugin_health("0.7.0.0", "0.8.0.0")

        self.assertEqual(missing.status, "missing")
        self.assertTrue(missing.repair_recommended)
        self.assertEqual(outdated.status, "outdated")
        self.assertTrue(outdated.repair_recommended)

    def test_current_or_newer_plugin_is_preserved(self) -> None:
        current = evaluate_streamdeck_plugin_health("0.8", "0.8.0.0")
        newer = evaluate_streamdeck_plugin_health("0.9.0.0", "0.8.0.0")

        self.assertEqual(current.status, "current")
        self.assertFalse(current.repair_recommended)
        self.assertEqual(newer.status, "newer")
        self.assertFalse(newer.repair_recommended)

    def test_missing_bundled_package_cannot_offer_repair(self) -> None:
        health = evaluate_streamdeck_plugin_health("0.8.0.0", None)
        self.assertEqual(health.status, "bundled_missing")
        self.assertFalse(health.repair_recommended)

