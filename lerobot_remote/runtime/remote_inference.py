"""Real LeRobot remote inference runtimes."""

from __future__ import annotations

from importlib import import_module
import threading
from typing import Any

from ..config.schema import PlatformConfig
from ..policies import build_lerobot_policy_server_config, build_lerobot_robot_client_config
from ..recording.metrics import EVENT_EXCEPTION, EVENT_RECOVERY, MetricEvent
from ..recording.recorder import JsonlMetricsRecorder
from ..reliability import STAGE_CLIENT_STARTUP, STAGE_SERVER_STARTUP, record_exception_event
from ..webui import DashboardState
from .common import (
    build_configured_metadata,
    copy_source_config,
    create_configured_run_dir,
    maybe_launch_dashboard,
)


def run_lerobot_policy_server(config: PlatformConfig) -> int:
    """Start a real LeRobot async inference policy server from platform config."""
    recorder: JsonlMetricsRecorder | None = None
    try:
        run_dir = create_configured_run_dir(config, "policy-server")
        metadata = build_configured_metadata("policy-server", config, run_dir)
        recorder = JsonlMetricsRecorder(run_dir, metadata=metadata)
        copy_source_config(config, run_dir)
        recorder.record_event(
            MetricEvent(
                EVENT_RECOVERY,
                "config-driven policy server startup configured",
                details={"stage": STAGE_SERVER_STARTUP, "component": "policy_server"},
            )
        )
        state = DashboardState.from_config(config, "policy-server")
        maybe_launch_dashboard(config, state, recorder)
        print(f"Run directory: {run_dir}")
        print(f"LeRobot policy server: {config.network.endpoint}")
        server_config = build_lerobot_policy_server_config(config)
        serve = _load_lerobot_serve()
        serve(server_config)
        recorder.write_summary()
        return 0
    except Exception as exc:
        if recorder is not None:
            record_exception_event(
                recorder,
                stage=STAGE_SERVER_STARTUP,
                component="policy_server",
                exc=exc,
            )
        raise
    finally:
        if recorder is not None:
            recorder.close()


def run_lerobot_robot_client(config: PlatformConfig) -> int:
    """Start a real LeRobot async inference robot client from platform config."""
    recorder: JsonlMetricsRecorder | None = None
    client = None
    action_receiver_thread: threading.Thread | None = None
    try:
        run_dir = create_configured_run_dir(config, "robot-client")
        metadata = build_configured_metadata("robot-client", config, run_dir)
        recorder = JsonlMetricsRecorder(run_dir, metadata=metadata)
        copy_source_config(config, run_dir)
        print(f"Run directory: {run_dir}")
        print(f"LeRobot robot client -> {config.network.endpoint}")

        client_config = build_lerobot_robot_client_config(config)
        RobotClient, _visualize = _load_lerobot_robot_client_api()
        client = RobotClient(client_config)
        if not client.start():
            recorder.record_event(
                MetricEvent(
                    EVENT_EXCEPTION,
                    "config-driven robot client failed to start",
                    severity="error",
                    details={"stage": STAGE_CLIENT_STARTUP, "component": "robot_client"},
                )
            )
            recorder.write_summary()
            return 1

        recorder.record_event(
            MetricEvent(
                EVENT_RECOVERY,
                "config-driven robot client startup complete",
                details={"stage": STAGE_CLIENT_STARTUP, "component": "robot_client"},
            )
        )
        action_receiver_thread = threading.Thread(target=client.receive_actions, daemon=True)
        action_receiver_thread.start()
        client.control_loop(config.experiment.task_name)
        recorder.write_summary()
        return 0
    except KeyboardInterrupt:
        if client is not None:
            client.stop()
        if action_receiver_thread is not None:
            action_receiver_thread.join()
        if recorder is not None:
            recorder.write_summary()
        return 0
    except Exception as exc:
        if recorder is not None:
            record_exception_event(
                recorder,
                stage=STAGE_CLIENT_STARTUP,
                component="robot_client",
                exc=exc,
            )
        raise
    finally:
        if recorder is not None:
            recorder.close()


def _load_lerobot_serve() -> Any:
    try:
        return import_module("lerobot.async_inference.policy_server").serve
    except ImportError as exc:
        raise RuntimeError(
            "LeRobot policy server is not available. Install lerobot before running "
            "config-driven remote inference server."
        ) from exc


def _load_lerobot_robot_client_api() -> tuple[type, Any]:
    try:
        RobotClient = import_module("lerobot.async_inference.robot_client").RobotClient
        visualize_action_queue_size = import_module(
            "lerobot.async_inference.helpers"
        ).visualize_action_queue_size
    except ImportError as exc:
        raise RuntimeError(
            "LeRobot robot client is not available. Install lerobot before running "
            "config-driven remote inference client."
        ) from exc
    return RobotClient, visualize_action_queue_size
