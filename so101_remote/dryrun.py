"""Deterministic dry-run helpers for validating metrics plumbing."""

from __future__ import annotations

from dataclasses import dataclass
import time
from pathlib import Path

from .metrics import (
    EVENT_RECOVERY,
    LATENCY_MS,
    LOOP_INTERVAL_MS,
    QUEUE_SIZE,
    MetricEvent,
    MetricSample,
)
from .recorder import JsonlMetricsRecorder, build_run_metadata, create_run_directory


@dataclass
class FakeRobotAdapter:
    """Hardware-free robot adapter used by dry-run execution."""

    robot_id: str = "dryrun-so101"
    connected: bool = False
    observations_read: int = 0
    actions_applied: int = 0

    def connect(self) -> None:
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def read_observation(self) -> dict[str, object]:
        self.observations_read += 1
        return {
            "sequence": self.observations_read,
            "timestamp": float(self.observations_read),
            "source": "dry-run",
        }

    def apply_action(self, action: object) -> None:
        self.actions_applied += 1


@dataclass
class FakePolicyAdapter:
    """Model-free policy adapter used by dry-run execution."""

    policy_type: str = "dryrun-policy"
    loaded: bool = False

    def load(self) -> None:
        self.loaded = True

    def infer_action(self, observation: dict[str, object]) -> dict[str, object]:
        return {
            "sequence": observation["sequence"],
            "command": "hold-position",
        }


def run_dry_run(root: str | Path | None = None, iterations: int = 5) -> Path:
    """Run a deterministic hardware-free pass and return the run directory."""
    run_dir = create_run_directory(root or Path("logs/experiments"), role="dry-run")
    robot = FakeRobotAdapter()
    policy = FakePolicyAdapter()
    created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(0))
    metadata = build_run_metadata(
        role="dry-run",
        created_at=created_at,
        robot={"id": robot.robot_id},
        policy={"type": policy.policy_type},
        extra={
            "validates_hardware": False,
            "validates_model": False,
            "purpose": "metrics plumbing only",
        },
    )

    with JsonlMetricsRecorder(run_dir, metadata=metadata) as recorder:
        robot.connect()
        policy.load()
        recorder.record_event(
            MetricEvent(
                EVENT_RECOVERY,
                "dry-run startup complete; metrics plumbing only",
                timestamp=0.0,
                details={"validates_hardware": "false", "validates_model": "false"},
            )
        )
        for index in range(iterations):
            observation = robot.read_observation()
            action = policy.infer_action(observation)
            robot.apply_action(action)
            timestamp = float(index + 1)
            recorder.record_sample(
                MetricSample(LOOP_INTERVAL_MS, 20.0 + index, "ms", timestamp=timestamp)
            )
            recorder.record_sample(
                MetricSample(LATENCY_MS, 5.0 + index, "ms", timestamp=timestamp)
            )
            recorder.record_sample(MetricSample(QUEUE_SIZE, float(index), "count", timestamp=timestamp))
        robot.disconnect()
        recorder.write_summary()

    return run_dir
