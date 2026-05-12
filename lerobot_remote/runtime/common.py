"""Shared helpers for config-driven runtimes."""

from __future__ import annotations

from pathlib import Path
import shutil

from ..config.schema import PlatformConfig
from ..policies import describe_lerobot_runtime
from ..recording.metrics import EVENT_EXCEPTION, MetricEvent
from ..recording.recorder import JsonlMetricsRecorder, build_run_metadata, create_run_directory
from ..webui import DashboardState, launch_dashboard


def configured_runtime_summary(role: str, config: PlatformConfig) -> dict[str, object]:
    """Return an operator-facing summary for a config-driven runtime."""
    summary: dict[str, object] = {"role": role, "config": config.summary()}
    if config.robot.type != "mock" and config.model.type != "mock":
        summary["lerobot"] = describe_lerobot_runtime(config)
    return summary


def build_configured_metadata(role: str, config: PlatformConfig, run_dir: Path) -> dict[str, object]:
    """Build reproducibility metadata for a config-driven runtime."""
    return build_run_metadata(
        role=role,
        server={"address": config.network.endpoint},
        robot={
            "type": config.robot.type,
            "id": config.robot.id,
            "port": config.robot.port,
            "cameras": sorted(config.camera.cameras),
        },
        policy={
            "type": config.model.type,
            "pretrained_name_or_path": config.model.model_path,
            "device": config.model.device,
            "dtype": config.model.dtype,
        },
        extra={
            "experiment": config.experiment.name,
            "mode": config.mode,
            "task_name": config.experiment.task_name,
            "run_dir": str(run_dir),
            "resolved_settings": configured_runtime_summary(role, config),
        },
    )


def create_configured_run_dir(config: PlatformConfig, role: str) -> Path:
    """Create the run directory for a config-driven runtime role."""
    return create_run_directory(config.experiment.save_dir, role=role)


def copy_source_config(config: PlatformConfig, run_dir: Path) -> None:
    """Copy the selected config into the run directory when available."""
    if config.source_path is not None and config.source_path.exists():
        shutil.copy2(config.source_path, run_dir / "config.yaml")


def maybe_launch_dashboard(
    config: PlatformConfig,
    state: DashboardState,
    recorder: JsonlMetricsRecorder,
) -> None:
    """Launch optional dashboard and record a warning if Gradio is unavailable."""
    dashboard = launch_dashboard(config, state)
    if dashboard is None and config.webui.enabled:
        recorder.record_event(
            MetricEvent(
                EVENT_EXCEPTION,
                "webui requested but gradio is not installed",
                severity="warning",
                details={"component": "webui"},
            )
        )


def disconnect_best_effort(device: object) -> None:
    """Disconnect hardware-like devices without masking the original error."""
    disconnect = getattr(device, "disconnect", None)
    if callable(disconnect):
        try:
            disconnect()
        except Exception:
            pass


def mock_joint_positions() -> dict[str, float]:
    """Return deterministic mock joint positions."""
    return {
        "shoulder_pan.pos": 0.0,
        "shoulder_lift.pos": -0.1,
        "elbow_flex.pos": 0.2,
        "wrist_flex.pos": 0.0,
        "wrist_roll.pos": 0.0,
        "gripper.pos": 0.5,
    }
