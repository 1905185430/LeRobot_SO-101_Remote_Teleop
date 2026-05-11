from __future__ import annotations

import unittest

from so101_remote.metrics import (
    EVENT_RECOVERY,
    EVENT_TIMEOUT,
    LATENCY_MS,
    MetricCollector,
    MetricEvent,
    MetricSample,
    compute_stats,
    derive_jitter_samples,
    format_terminal_summary,
)


class MetricTests(unittest.TestCase):
    def test_metric_sample_to_dict_preserves_fields(self) -> None:
        sample = MetricSample(LATENCY_MS, 12.5, "ms", timestamp=1.0, tags={"role": "client"})

        self.assertEqual(
            sample.to_dict(),
            {
                "name": LATENCY_MS,
                "value": 12.5,
                "unit": "ms",
                "timestamp": 1.0,
                "tags": {"role": "client"},
            },
        )

    def test_metric_event_to_dict_preserves_fields(self) -> None:
        event = MetricEvent(
            EVENT_TIMEOUT,
            "heartbeat missed",
            timestamp=2.0,
            severity="warning",
            details={"endpoint": "server"},
        )

        self.assertEqual(event.to_dict()["event_type"], EVENT_TIMEOUT)
        self.assertEqual(event.to_dict()["severity"], "warning")
        self.assertEqual(event.to_dict()["details"], {"endpoint": "server"})

    def test_compute_stats_uses_nearest_rank_p95(self) -> None:
        stats = compute_stats([1, 2, 3, 4, 100])

        self.assertEqual(stats.count, 5)
        self.assertEqual(stats.min, 1)
        self.assertEqual(stats.max, 100)
        self.assertEqual(stats.mean, 22)
        self.assertEqual(stats.p95, 100)

    def test_compute_stats_handles_empty_values(self) -> None:
        stats = compute_stats([])

        self.assertEqual(stats.count, 0)
        self.assertIsNone(stats.min)
        self.assertIsNone(stats.max)
        self.assertIsNone(stats.mean)
        self.assertIsNone(stats.p95)

    def test_derive_jitter_samples(self) -> None:
        samples = [
            MetricSample(LATENCY_MS, 10, "ms", timestamp=1.0),
            MetricSample(LATENCY_MS, 15, "ms", timestamp=2.0),
            MetricSample(LATENCY_MS, 12, "ms", timestamp=3.0),
        ]

        jitter = derive_jitter_samples(samples)

        self.assertEqual([sample.value for sample in jitter], [5, 3])
        self.assertEqual([sample.unit for sample in jitter], ["ms", "ms"])
        self.assertEqual([sample.timestamp for sample in jitter], [2.0, 3.0])

    def test_collector_counts_events(self) -> None:
        collector = MetricCollector()
        collector.record_event(EVENT_TIMEOUT, "missed heartbeat")
        collector.record_event(EVENT_RECOVERY, "stream recovered")
        collector.record_event(EVENT_TIMEOUT, "missed heartbeat again")

        self.assertEqual(collector.event_counts(), {EVENT_TIMEOUT: 2, EVENT_RECOVERY: 1})

    def test_terminal_summary_includes_metric_stats_and_events(self) -> None:
        collector = MetricCollector()
        collector.record_sample(LATENCY_MS, 10, "ms")
        collector.record_sample(LATENCY_MS, 20, "ms")
        collector.record_event(EVENT_TIMEOUT, "missed heartbeat")

        summary = format_terminal_summary(collector.stats_by_name(), collector.event_counts())

        self.assertIn("Metrics summary", summary)
        self.assertIn("latency_ms", summary)
        self.assertIn("count=", summary)
        self.assertIn("mean=", summary)
        self.assertIn("p95=", summary)
        self.assertIn("timeout=1", summary)


if __name__ == "__main__":
    unittest.main()
