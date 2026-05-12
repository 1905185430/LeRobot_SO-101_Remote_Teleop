from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from lerobot_remote.recording.metrics import EVENT_TIMEOUT, LATENCY_MS, MetricEvent, MetricSample
from lerobot_remote.recording.recorder import (
    JsonlMetricsRecorder,
    build_run_metadata,
    create_run_directory,
)


class RecorderTests(unittest.TestCase):
    def test_create_run_directory_is_unique(self) -> None:
        with TemporaryDirectory() as tmpdir:
            now = datetime(2026, 5, 11, 3, 0, 0, tzinfo=timezone.utc)

            first = create_run_directory(tmpdir, role="client", now=now)
            second = create_run_directory(tmpdir, role="client", now=now)

            self.assertNotEqual(first, second)
            self.assertTrue(first.exists())
            self.assertTrue(second.exists())
            self.assertEqual(first.parent, Path(tmpdir))
            self.assertIn("20260511-030000-client-", first.name)

    def test_build_run_metadata_has_reproducibility_keys(self) -> None:
        metadata = build_run_metadata(
            role="client",
            created_at="2026-05-11T03:00:00+00:00",
            server={"address": "127.0.0.1:8080"},
            robot={"id": "so101_follower"},
            policy={"type": "smolvla"},
            extra={"note": "dry-run"},
            git_commit="abc1234",
        )

        self.assertEqual(
            set(metadata),
            {"role", "created_at", "server", "robot", "policy", "extra", "git_commit"},
        )
        self.assertEqual(metadata["role"], "client")
        self.assertEqual(metadata["git_commit"], "abc1234")

    def test_recorder_writes_metadata_metrics_events_and_csv(self) -> None:
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run"
            metadata = build_run_metadata(
                role="client",
                created_at="2026-05-11T03:00:00+00:00",
                git_commit="abc1234",
            )

            with JsonlMetricsRecorder(run_dir, metadata=metadata) as recorder:
                recorder.record_sample(MetricSample(LATENCY_MS, 12.5, "ms", timestamp=1.0))
                recorder.record_event(MetricEvent(EVENT_TIMEOUT, "heartbeat missed"))

            metadata_text = (run_dir / "metadata.json").read_text(encoding="utf-8")
            metrics_text = (run_dir / "metrics.jsonl").read_text(encoding="utf-8")
            events_text = (run_dir / "events.jsonl").read_text(encoding="utf-8")
            csv_text = (run_dir / "metrics.csv").read_text(encoding="utf-8")

            self.assertEqual(json.loads(metadata_text)["role"], "client")
            self.assertIn('"name": "latency_ms"', metrics_text)
            self.assertIn('"event_type": "timeout"', events_text)
            self.assertTrue(csv_text.startswith("timestamp,name,value,unit,tags"))

    def test_write_summary_markdown_contains_stats_events_and_files(self) -> None:
        with TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run"
            metadata = build_run_metadata(
                role="client",
                created_at="2026-05-11T03:00:00+00:00",
                git_commit="abc1234",
            )

            with JsonlMetricsRecorder(run_dir, metadata=metadata) as recorder:
                recorder.record_sample(MetricSample(LATENCY_MS, 10, "ms"))
                recorder.record_sample(MetricSample(LATENCY_MS, 20, "ms"))
                recorder.record_sample(MetricSample(LATENCY_MS, 30, "ms"))
                recorder.record_event(MetricEvent(EVENT_TIMEOUT, "heartbeat missed"))
                summary_path = recorder.write_summary()

            summary = summary_path.read_text(encoding="utf-8")
            self.assertIn("# Run Summary", summary)
            self.assertIn("latency_ms", summary)
            self.assertIn("| Metric | Unit | Count | Min | Max | Mean | P95 |", summary)
            self.assertIn("timeout", summary)
            self.assertIn("metadata.json", summary)
            self.assertIn("metrics.jsonl", summary)
            self.assertIn("events.jsonl", summary)


if __name__ == "__main__":
    unittest.main()
