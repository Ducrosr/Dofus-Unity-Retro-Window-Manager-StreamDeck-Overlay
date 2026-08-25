from __future__ import annotations

import unittest

from dwm.services.performance import RuntimeMetrics, adaptive_refresh_delay_seconds


class PerformanceTests(unittest.TestCase):
    def test_adaptive_refresh_uses_recovery_scans_when_event_hook_is_healthy(self) -> None:
        self.assertEqual(
            adaptive_refresh_delay_seconds(
                10,
                enabled=True,
                event_hook_healthy=True,
                has_windows=True,
            ),
            60,
        )
        self.assertEqual(
            adaptive_refresh_delay_seconds(
                10,
                enabled=True,
                event_hook_healthy=True,
                has_windows=False,
            ),
            20,
        )

    def test_base_interval_is_restored_without_a_healthy_hook(self) -> None:
        self.assertEqual(
            adaptive_refresh_delay_seconds(
                7,
                enabled=True,
                event_hook_healthy=False,
                has_windows=True,
            ),
            7,
        )
        self.assertEqual(
            adaptive_refresh_delay_seconds(
                7,
                enabled=False,
                event_hook_healthy=True,
                has_windows=True,
            ),
            7,
        )

    def test_runtime_metrics_keep_bounded_summaries_and_failures(self) -> None:
        metrics = RuntimeMetrics(sample_limit=2)
        metrics.record_scan(0.010)
        metrics.record_scan(0.020)
        metrics.record_scan(0.030)
        metrics.record_focus(0.004, succeeded=True)
        metrics.record_focus(0.006, succeeded=False)

        scan = metrics.scan_summary()
        self.assertEqual(scan.count, 2)
        self.assertAlmostEqual(scan.average_ms, 25.0)
        self.assertAlmostEqual(scan.maximum_ms, 30.0)
        self.assertEqual(metrics.focus_failures, 1)
        self.assertIn("5.0 ms en moyenne", metrics.focus_summary().format())

