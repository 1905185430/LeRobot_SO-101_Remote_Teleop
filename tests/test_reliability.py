from __future__ import annotations

import unittest

from so101_remote.metrics import EVENT_EXCEPTION, MetricCollector
from so101_remote.reliability import (
    STAGE_SERIAL_PORT,
    STAGE_SERVER_STARTUP,
    record_exception_event,
)


class ReliabilityTests(unittest.TestCase):
    def test_record_exception_event_builds_diagnostic_event(self) -> None:
        exc = RuntimeError("serial unavailable")

        event = record_exception_event(
            object(),
            stage=STAGE_SERIAL_PORT,
            component="so101",
            exc=exc,
        )

        self.assertEqual(event.event_type, EVENT_EXCEPTION)
        self.assertEqual(event.severity, "error")
        self.assertIn("so101 failed during serial_port", event.message)
        self.assertIn("RuntimeError: serial unavailable", event.message)
        self.assertEqual(
            event.details,
            {
                "stage": STAGE_SERIAL_PORT,
                "component": "so101",
                "exception_type": "RuntimeError",
                "message": "serial unavailable",
            },
        )

    def test_record_exception_event_records_to_metric_collector(self) -> None:
        collector = MetricCollector()

        event = record_exception_event(
            collector,
            stage=STAGE_SERVER_STARTUP,
            component="policy_server",
            exc=ValueError("bad model path"),
            severity="critical",
        )

        self.assertEqual(collector.events, [event])
        self.assertEqual(collector.event_counts(), {EVENT_EXCEPTION: 1})
        self.assertEqual(collector.events[0].severity, "critical")


if __name__ == "__main__":
    unittest.main()
