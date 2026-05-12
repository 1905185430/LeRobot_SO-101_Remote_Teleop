"""Reliability event helpers for runtime diagnostics."""

from __future__ import annotations

from collections.abc import Callable
from inspect import signature
import time
from typing import TypeVar

from .recording.metrics import EVENT_EXCEPTION, EVENT_RECOVERY, EVENT_RETRY, MetricEvent

STAGE_SERVER_STARTUP = "server_startup"
STAGE_CLIENT_STARTUP = "client_startup"
STAGE_MODEL_PATH = "model_path"
STAGE_CAMERA = "camera"
STAGE_SERIAL_PORT = "serial_port"
STAGE_NETWORK = "network"
STAGE_TIMEOUT = "timeout"

T = TypeVar("T")


def record_exception_event(
    collector_or_recorder: object,
    *,
    stage: str,
    component: str,
    exc: BaseException,
    severity: str = "error",
) -> MetricEvent:
    """Record an exception event with diagnostic context."""
    exception_type = type(exc).__name__
    message = str(exc)
    event = MetricEvent(
        EVENT_EXCEPTION,
        f"{component} failed during {stage}: {exception_type}: {message}",
        severity=severity,
        details={
            "stage": stage,
            "component": component,
            "exception_type": exception_type,
            "message": message,
        },
    )
    _record_event(collector_or_recorder, event)
    return event


def run_with_retries(
    operation: Callable[[], T],
    collector_or_recorder: object,
    *,
    attempts: int = 3,
    component: str,
    stage: str,
    sleep_s: float = 0.0,
) -> T:
    """Run an operation with bounded retry and recovery event recording."""
    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    failures = 0
    for attempt in range(1, attempts + 1):
        try:
            result = operation()
        except Exception as exc:
            failures += 1
            if attempt >= attempts:
                record_exception_event(
                    collector_or_recorder,
                    stage=stage,
                    component=component,
                    exc=exc,
                )
                raise

            retry_event = MetricEvent(
                EVENT_RETRY,
                f"Retrying {component} during {stage} after {type(exc).__name__}: {exc}",
                severity="warning",
                details={
                    "attempt": str(attempt),
                    "attempts": str(attempts),
                    "component": component,
                    "stage": stage,
                    "exception_type": type(exc).__name__,
                    "message": str(exc),
                },
            )
            _record_event(collector_or_recorder, retry_event)
            if sleep_s > 0:
                time.sleep(sleep_s)
            continue

        if failures:
            _record_event(
                collector_or_recorder,
                MetricEvent(
                    EVENT_RECOVERY,
                    f"{component} recovered during {stage} after {failures} failure(s)",
                    details={
                        "attempt": str(attempt),
                        "attempts": str(attempts),
                        "component": component,
                        "stage": stage,
                    },
                ),
            )
        return result

    raise RuntimeError("unreachable retry state")


def _record_event(collector_or_recorder: object, event: MetricEvent) -> None:
    record_event = getattr(collector_or_recorder, "record_event", None)
    if record_event is None:
        return

    parameters = signature(record_event).parameters
    if len(parameters) == 1:
        record_event(event)
        return

    record_event(
        event.event_type,
        event.message,
        event.timestamp,
        event.severity,
        event.details,
    )
