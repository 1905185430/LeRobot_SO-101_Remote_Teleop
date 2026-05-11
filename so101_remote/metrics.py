"""Communication metric models and summary helpers."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from math import ceil
from typing import Iterable, Mapping, Sequence

LATENCY_MS = "latency_ms"
RTT_MS = "rtt_ms"
JITTER_MS = "jitter_ms"
LOOP_INTERVAL_MS = "loop_interval_ms"
CHUNK_INTERVAL_MS = "chunk_interval_ms"
QUEUE_SIZE = "queue_size"

EVENT_TIMEOUT = "timeout"
EVENT_DISCONNECT = "disconnect"
EVENT_RETRY = "retry"
EVENT_RECOVERY = "recovery"
EVENT_EXCEPTION = "exception"


@dataclass(frozen=True)
class MetricSample:
    """A numeric runtime measurement."""

    name: str
    value: float
    unit: str
    timestamp: float | None = None
    tags: dict[str, str] | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "tags": dict(self.tags or {}),
        }


@dataclass(frozen=True)
class MetricEvent:
    """A structured non-numeric runtime event."""

    event_type: str
    message: str
    timestamp: float | None = None
    severity: str = "info"
    details: dict[str, str] | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "event_type": self.event_type,
            "message": self.message,
            "timestamp": self.timestamp,
            "severity": self.severity,
            "details": dict(self.details or {}),
        }


@dataclass(frozen=True)
class MetricStats:
    """Aggregate statistics for a numeric metric."""

    count: int
    min: float | None
    max: float | None
    mean: float | None
    p95: float | None


def compute_stats(values: Iterable[float]) -> MetricStats:
    """Compute deterministic count/min/max/mean/p95 statistics."""
    ordered = sorted(float(value) for value in values)
    count = len(ordered)
    if count == 0:
        return MetricStats(count=0, min=None, max=None, mean=None, p95=None)

    p95_index = max(0, min(count - 1, ceil(0.95 * count) - 1))
    return MetricStats(
        count=count,
        min=ordered[0],
        max=ordered[-1],
        mean=sum(ordered) / count,
        p95=ordered[p95_index],
    )


def derive_jitter_samples(
    samples: Sequence[MetricSample], name: str = JITTER_MS
) -> list[MetricSample]:
    """Derive absolute adjacent deltas from ordered metric samples."""
    if len(samples) < 2:
        return []

    if all(sample.timestamp is not None for sample in samples):
        ordered = sorted(samples, key=lambda sample: sample.timestamp or 0.0)
    else:
        ordered = list(samples)

    jitter: list[MetricSample] = []
    for previous, current in zip(ordered, ordered[1:]):
        jitter.append(
            MetricSample(
                name=name,
                value=abs(current.value - previous.value),
                unit=current.unit,
                timestamp=current.timestamp,
                tags=dict(current.tags or {}),
            )
        )
    return jitter


def count_events(events: Iterable[MetricEvent]) -> dict[str, int]:
    """Count events by stable event type."""
    return dict(Counter(event.event_type for event in events))


class MetricCollector:
    """In-memory collector used by runtime code and tests."""

    def __init__(self) -> None:
        self.samples: list[MetricSample] = []
        self.events: list[MetricEvent] = []

    def record_sample(
        self,
        name: str,
        value: float,
        unit: str,
        timestamp: float | None = None,
        tags: dict[str, str] | None = None,
    ) -> MetricSample:
        sample = MetricSample(name, float(value), unit, timestamp, tags)
        self.samples.append(sample)
        return sample

    def record_event(
        self,
        event_type: str,
        message: str,
        timestamp: float | None = None,
        severity: str = "info",
        details: dict[str, str] | None = None,
    ) -> MetricEvent:
        event = MetricEvent(event_type, message, timestamp, severity, details)
        self.events.append(event)
        return event

    def extend_samples(self, samples: Iterable[MetricSample]) -> None:
        self.samples.extend(samples)

    def stats_by_name(self) -> dict[str, MetricStats]:
        grouped: dict[str, list[float]] = defaultdict(list)
        for sample in self.samples:
            grouped[sample.name].append(sample.value)
        return {name: compute_stats(values) for name, values in grouped.items()}

    def event_counts(self) -> dict[str, int]:
        return count_events(self.events)


def format_terminal_summary(
    stats_by_name: Mapping[str, MetricStats],
    event_counts: Mapping[str, int] | None = None,
) -> str:
    """Format a deterministic human-readable metrics summary."""
    lines = ["Metrics summary"]
    for name in sorted(stats_by_name):
        stats = stats_by_name[name]
        lines.append(
            f"{name}: count={stats.count} min={_fmt(stats.min)} max={_fmt(stats.max)} "
            f"mean={_fmt(stats.mean)} p95={_fmt(stats.p95)}"
        )

    if event_counts:
        event_text = ", ".join(
            f"{event_type}={event_counts[event_type]}" for event_type in sorted(event_counts)
        )
        lines.append(f"Events: {event_text}")

    return "\n".join(lines)


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}".rstrip("0").rstrip(".")
