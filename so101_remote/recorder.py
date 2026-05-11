"""Experiment run artifact recording helpers."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from types import TracebackType
from typing import Iterable, Mapping
from uuid import uuid4

from .metrics import MetricEvent, MetricSample

DEFAULT_RUN_ROOT = Path("logs/experiments")


def current_git_commit() -> str | None:
    """Return the current short git commit when available."""
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    commit = result.stdout.strip()
    return commit or None


def create_run_directory(
    root: str | Path = DEFAULT_RUN_ROOT,
    role: str = "run",
    now: datetime | None = None,
) -> Path:
    """Create a unique local experiment run directory."""
    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)
    created_at = now or datetime.now(timezone.utc)
    stamp = created_at.strftime("%Y%m%d-%H%M%S")

    while True:
        run_dir = root_path / f"{stamp}-{role}-{uuid4().hex[:8]}"
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
            return run_dir
        except FileExistsError:
            continue


def build_run_metadata(
    *,
    role: str,
    created_at: datetime | str | None = None,
    server: Mapping[str, object] | None = None,
    robot: Mapping[str, object] | None = None,
    policy: Mapping[str, object] | None = None,
    extra: Mapping[str, object] | None = None,
    git_commit: str | None = None,
) -> dict[str, object]:
    """Build reproducibility metadata for a local experiment run."""
    if created_at is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    elif isinstance(created_at, datetime):
        timestamp = created_at.isoformat()
    else:
        timestamp = created_at

    return {
        "role": role,
        "created_at": timestamp,
        "server": dict(server or {}),
        "robot": dict(robot or {}),
        "policy": dict(policy or {}),
        "extra": dict(extra or {}),
        "git_commit": git_commit if git_commit is not None else current_git_commit(),
    }


class JsonlMetricsRecorder:
    """Append metrics and events to a run directory as JSONL and CSV."""

    def __init__(
        self,
        run_dir: str | Path,
        metadata: Mapping[str, object] | None = None,
        write_csv: bool = True,
    ) -> None:
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.metadata = dict(metadata or {})
        self.write_csv = write_csv
        self.samples: list[MetricSample] = []
        self.events: list[MetricEvent] = []

        self.metadata_path = self.run_dir / "metadata.json"
        self.metrics_path = self.run_dir / "metrics.jsonl"
        self.events_path = self.run_dir / "events.jsonl"
        self.csv_path = self.run_dir / "metrics.csv"

        if metadata is not None:
            self.metadata_path.write_text(
                json.dumps(self.metadata, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

        self._metrics_file = self.metrics_path.open("a", encoding="utf-8", buffering=1)
        self._events_file = self.events_path.open("a", encoding="utf-8", buffering=1)
        self._csv_file = None
        self._csv_writer = None
        if self.write_csv:
            new_csv = not self.csv_path.exists() or self.csv_path.stat().st_size == 0
            self._csv_file = self.csv_path.open("a", newline="", encoding="utf-8", buffering=1)
            self._csv_writer = csv.writer(self._csv_file)
            if new_csv:
                self._csv_writer.writerow(["timestamp", "name", "value", "unit", "tags"])
                self._csv_file.flush()

    def record_sample(self, sample: MetricSample) -> None:
        self.samples.append(sample)
        self._metrics_file.write(json.dumps(sample.to_dict(), sort_keys=True) + "\n")
        self._metrics_file.flush()

        if self._csv_writer is not None and self._csv_file is not None:
            self._csv_writer.writerow(
                [
                    "" if sample.timestamp is None else sample.timestamp,
                    sample.name,
                    sample.value,
                    sample.unit,
                    json.dumps(sample.tags or {}, sort_keys=True),
                ]
            )
            self._csv_file.flush()

    def record_event(self, event: MetricEvent) -> None:
        self.events.append(event)
        self._events_file.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")
        self._events_file.flush()

    def record_samples(self, samples: Iterable[MetricSample]) -> None:
        for sample in samples:
            self.record_sample(sample)

    def record_events(self, events: Iterable[MetricEvent]) -> None:
        for event in events:
            self.record_event(event)

    def close(self) -> None:
        self._metrics_file.close()
        self._events_file.close()
        if self._csv_file is not None:
            self._csv_file.close()

    def __enter__(self) -> JsonlMetricsRecorder:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
