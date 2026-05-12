from __future__ import annotations

import unittest

from lerobot_remote.recording.metrics import EVENT_EXCEPTION, EVENT_RECOVERY, EVENT_RETRY, MetricCollector
from lerobot_remote.reliability import (
    STAGE_NETWORK,
    STAGE_SERIAL_PORT,
    STAGE_SERVER_STARTUP,
    record_exception_event,
    run_with_retries,
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

    def test_run_with_retries_records_retry_and_recovery(self) -> None:
        collector = MetricCollector()
        calls = 0

        def operation() -> str:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise RuntimeError("connection warming up")
            return "connected"

        result = run_with_retries(
            operation,
            collector,
            attempts=2,
            component="robot_client",
            stage=STAGE_NETWORK,
        )

        self.assertEqual(result, "connected")
        self.assertEqual(calls, 2)
        self.assertEqual(collector.event_counts(), {EVENT_RETRY: 1, EVENT_RECOVERY: 1})
        retry_event, recovery_event = collector.events
        self.assertEqual(retry_event.severity, "warning")
        self.assertIn("Retrying robot_client during network", retry_event.message)
        self.assertEqual(retry_event.details["attempt"], "1")
        self.assertEqual(retry_event.details["attempts"], "2")
        self.assertEqual(retry_event.details["exception_type"], "RuntimeError")
        self.assertIn("robot_client recovered during network", recovery_event.message)

    def test_run_with_retries_records_exception_and_reraises(self) -> None:
        collector = MetricCollector()

        def operation() -> str:
            raise TimeoutError("no response")

        with self.assertRaises(TimeoutError):
            run_with_retries(
                operation,
                collector,
                attempts=2,
                component="policy_server",
                stage=STAGE_NETWORK,
            )

        self.assertEqual(collector.event_counts(), {EVENT_RETRY: 1, EVENT_EXCEPTION: 1})
        exception_event = collector.events[-1]
        self.assertEqual(exception_event.details["component"], "policy_server")
        self.assertEqual(exception_event.details["stage"], STAGE_NETWORK)
        self.assertEqual(exception_event.details["exception_type"], "TimeoutError")
        self.assertEqual(exception_event.details["message"], "no response")


if __name__ == "__main__":
    unittest.main()
