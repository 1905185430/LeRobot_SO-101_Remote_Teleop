"""Dashboard state shared by runtime code and WebUI."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import threading
import time
from typing import Any, Mapping

from ..config.schema import PlatformConfig


@dataclass
class DashboardState:
    """Thread-safe state shared between runtime code and a read-only dashboard."""

    experiment_name: str
    mode: str
    role: str
    model_type: str
    robot_type: str
    endpoint: str
    connection_status: str = "starting"
    latest_images: dict[str, str] = field(default_factory=dict)
    latest_joint_states: dict[str, float] = field(default_factory=dict)
    latest_action: dict[str, float] = field(default_factory=dict)
    latest_latency_ms: float | None = None
    latest_inference_ms: float | None = None
    events: list[str] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @classmethod
    def from_config(cls, config: PlatformConfig, role: str) -> DashboardState:
        """Create initial dashboard state from a platform config."""
        return cls(
            experiment_name=config.experiment.name,
            mode=config.mode,
            role=role,
            model_type=config.model.type,
            robot_type=config.robot.type,
            endpoint=config.network.endpoint,
        )

    def update_connection(self, status: str) -> None:
        with self._lock:
            self.connection_status = status
            self._append_event_locked(f"connection: {status}")

    def update_observation(self, observation: Mapping[str, Any]) -> None:
        """Update state from an OBSERVATION-like mapping."""
        with self._lock:
            joints = observation.get("joint_positions", {})
            images = observation.get("images", {})
            if isinstance(joints, Mapping):
                self.latest_joint_states = {str(key): float(value) for key, value in joints.items()}
            if isinstance(images, Mapping):
                self.latest_images = {str(key): str(value) for key, value in images.items()}
            self._append_event_locked(f"observation frame={observation.get('frame_id', '')}")

    def update_action(self, action_message: Mapping[str, Any]) -> None:
        """Update state from an ACTION-like mapping."""
        with self._lock:
            action = action_message.get("action", {})
            if isinstance(action, Mapping):
                self.latest_action = {str(key): float(value) for key, value in action.items()}
            self._append_event_locked(f"action frame={action_message.get('frame_id', '')}")

    def update_latency(self, latency_ms: float, inference_ms: float | None = None) -> None:
        with self._lock:
            self.latest_latency_ms = float(latency_ms)
            if inference_ms is not None:
                self.latest_inference_ms = float(inference_ms)

    def log(self, message: str) -> None:
        with self._lock:
            self._append_event_locked(message)

    def snapshot(self) -> dict[str, object]:
        """Return a stable copy for rendering or tests."""
        with self._lock:
            return {
                "experiment_name": self.experiment_name,
                "mode": self.mode,
                "role": self.role,
                "model_type": self.model_type,
                "robot_type": self.robot_type,
                "endpoint": self.endpoint,
                "connection_status": self.connection_status,
                "latest_images": dict(self.latest_images),
                "latest_joint_states": dict(self.latest_joint_states),
                "latest_action": dict(self.latest_action),
                "latest_latency_ms": self.latest_latency_ms,
                "latest_inference_ms": self.latest_inference_ms,
                "events": list(self.events),
            }

    def _append_event_locked(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.events.append(f"{timestamp} {message}")
        del self.events[:-50]


def snapshot_json(state: DashboardState) -> str:
    """Return dashboard state as deterministic JSON for logs and debugging."""
    return json.dumps(state.snapshot(), indent=2, sort_keys=True)
