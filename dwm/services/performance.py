from __future__ import annotations

from collections import deque
from dataclasses import dataclass


def adaptive_refresh_delay_seconds(
    base_seconds: object,
    *,
    enabled: bool,
    event_hook_healthy: bool,
    has_windows: bool,
) -> int:
    try:
        base = int(base_seconds)
    except (TypeError, ValueError):
        base = 10
    base = max(2, min(300, base))
    if not enabled or not event_hook_healthy:
        return base
    recovery_interval = 60 if has_windows else 20
    return min(300, max(base, recovery_interval))


@dataclass(frozen=True)
class MetricSummary:
    count: int
    last_ms: float
    average_ms: float
    maximum_ms: float

    def format(self) -> str:
        if not self.count:
            return "aucune mesure"
        return (
            f"{self.average_ms:.1f} ms en moyenne · "
            f"{self.last_ms:.1f} ms dernière · {self.maximum_ms:.1f} ms max"
        )


class RuntimeMetrics:
    def __init__(self, sample_limit: int = 60):
        limit = max(1, int(sample_limit))
        self._scan_ms: deque[float] = deque(maxlen=limit)
        self._focus_ms: deque[float] = deque(maxlen=limit)
        self.focus_failures = 0

    @staticmethod
    def _summary(samples: deque[float]) -> MetricSummary:
        if not samples:
            return MetricSummary(0, 0.0, 0.0, 0.0)
        values = tuple(samples)
        return MetricSummary(
            len(values),
            values[-1],
            sum(values) / len(values),
            max(values),
        )

    def record_scan(self, elapsed_seconds: float) -> None:
        self._scan_ms.append(max(0.0, float(elapsed_seconds)) * 1000.0)

    def record_focus(self, elapsed_seconds: float, *, succeeded: bool) -> None:
        self._focus_ms.append(max(0.0, float(elapsed_seconds)) * 1000.0)
        if not succeeded:
            self.focus_failures += 1

    def scan_summary(self) -> MetricSummary:
        return self._summary(self._scan_ms)

    def focus_summary(self) -> MetricSummary:
        return self._summary(self._focus_ms)

