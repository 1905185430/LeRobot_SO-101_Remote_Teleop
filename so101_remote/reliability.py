"""Reliability event helpers for runtime diagnostics."""

from __future__ import annotations

from collections.abc import Callable
from inspect import signature
import time
from typing import TypeVar

from .metrics import EVENT_EXCEPTION, EVENT_RECOVERY, EVENT_RETRY, MetricEvent

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
