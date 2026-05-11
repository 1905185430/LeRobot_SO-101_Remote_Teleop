"""Optional server-side WebUI state and Gradio dashboard helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
import html
from importlib import import_module
import json
import threading
import time
from typing import Any, Mapping

from .config_schema import PlatformConfig


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


def launch_dashboard(config: PlatformConfig, state: DashboardState):
    """Launch an optional Gradio dashboard and return the app object.

    Gradio is intentionally optional. If it is not installed, this returns `None`
    and records a state event so robotics runtime startup can continue.
    """
    if not config.webui.enabled:
        return None
    try:
        gr = import_module("gradio")
    except ImportError:
        state.log("webui disabled because gradio is not installed")
        return None

    app = gr.Blocks(title=f"{config.experiment.name} dashboard")
    with app:
        gr.Markdown(f"# {config.experiment.name}")
        status = gr.JSON(label="Runtime")
        images = gr.HTML(label="Images")
        joints = gr.JSON(label="Joint State")
        action = gr.JSON(label="Latest Action")
        metrics = gr.JSON(label="Metrics")
        logs = gr.Textbox(label="Events", lines=12)
        refresh = gr.Button("Refresh")

        def render():
            return render_dashboard_snapshot(state)

        refresh.click(render, outputs=[status, images, joints, action, metrics, logs])

    app.launch(
        server_name=config.webui.host,
        server_port=config.webui.port,
        prevent_thread_lock=True,
        quiet=True,
    )
    state.log(f"webui listening on {config.webui.host}:{config.webui.port}")
    return app


def render_dashboard_snapshot(state: DashboardState) -> tuple[dict[str, object], str, dict[str, float], dict[str, float], dict[str, object], str]:
    """Render dashboard state into Gradio component values."""
    snapshot = state.snapshot()
    status = {
        "experiment": snapshot["experiment_name"],
        "mode": snapshot["mode"],
        "role": snapshot["role"],
        "model": snapshot["model_type"],
        "robot": snapshot["robot_type"],
        "endpoint": snapshot["endpoint"],
        "connection_status": snapshot["connection_status"],
    }
    metrics = {
        "latency_ms": snapshot["latest_latency_ms"],
        "inference_ms": snapshot["latest_inference_ms"],
        "image_count": len(snapshot["latest_images"]),
    }
    logs = "\n".join(str(event) for event in snapshot["events"])
    return (
        status,
        render_images_html(snapshot["latest_images"]),
        snapshot["latest_joint_states"],
        snapshot["latest_action"],
        metrics,
        logs,
    )


def render_images_html(images: Mapping[str, str]) -> str:
    """Render base64 image payloads as simple HTML."""
    if not images:
        return "<p>No images received.</p>"
    blocks: list[str] = []
    for name, payload in sorted(images.items()):
        safe_name = html.escape(str(name))
        safe_payload = html.escape(str(payload))
        if safe_payload.startswith("data:image/"):
            src = safe_payload
        else:
            src = f"data:image/jpeg;base64,{safe_payload}"
        blocks.append(
            "<figure style='display:inline-block;margin:8px'>"
            f"<figcaption>{safe_name}</figcaption>"
            f"<img src='{src}' style='max-width:320px;max-height:240px;border:1px solid #ddd' />"
            "</figure>"
        )
    return "\n".join(blocks)


def snapshot_json(state: DashboardState) -> str:
    """Return dashboard state as deterministic JSON for logs and debugging."""
    return json.dumps(state.snapshot(), indent=2, sort_keys=True)
