"""Config-driven runtime dispatch for real and mock execution paths."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
import shutil
import threading
import time
from typing import Any

from .config_schema import PlatformConfig
from .lerobot_factory import (
    build_lerobot_policy_server_config,
    build_lerobot_robot_client_config,
    describe_lerobot_runtime,
)
from .metrics import EVENT_EXCEPTION, EVENT_RECOVERY, LATENCY_MS, MetricEvent, MetricSample
from .network.protocol import make_observation_message
from .network.tcp_client import TcpClient
from .network.tcp_server import TcpServer, mirror_joint_action
from .recorder import JsonlMetricsRecorder, build_run_metadata, create_run_directory
from .reliability import (
    STAGE_CLIENT_STARTUP,
    STAGE_NETWORK,
    STAGE_SERVER_STARTUP,
    record_exception_event,
)
from .teleop_tcp import (
    TcpTeleopFollowerServer,
    TcpTeleopLeaderClient,
    build_teleop_follower_robot,
    build_teleop_leader_device,
    tcp_teleop_settings,
)
from .webui import DashboardState, launch_dashboard


def configured_runtime_summary(role: str, config: PlatformConfig) -> dict[str, object]:
    """Return an operator-facing summary for a config-driven runtime."""
    summary: dict[str, object] = {"role": role, "config": config.summary()}
    if config.robot.type != "mock" and config.model.type != "mock":
        summary["lerobot"] = describe_lerobot_runtime(config)
    return summary


def run_configured_server(config: PlatformConfig) -> int:
    """Run the configured server role."""
    if config.mode == "debug_mock":
        return run_mock_tcp_server(config)
    if config.mode == "remote_inference":
        return run_lerobot_policy_server(config)
    if config.mode == "remote_teleoperation":
        return run_tcp_teleop_follower_server(config)
    raise RuntimeError(f"Config mode '{config.mode}' is not a server runtime mode.")


def run_configured_client(config: PlatformConfig) -> int:
    """Run the configured client role."""
    if config.mode == "debug_mock":
        return run_mock_tcp_client(config)
    if config.mode == "remote_inference":
        return run_lerobot_robot_client(config)
    if config.mode == "remote_teleoperation":
        return run_tcp_teleop_leader_client(config)
    raise RuntimeError(f"Config mode '{config.mode}' is not a client runtime mode.")


def run_configured_local(config: PlatformConfig) -> int:
    """Run the configured local role."""
    if config.mode == "debug_mock":
        return run_local_mock_loop(config)
    if config.mode == "local_inference":
        raise RuntimeError(
            "Config-driven local LeRobot inference runtime is not implemented yet. "
            "Use --dry-run to validate local config, or run remote_inference server/client for the "
            "first real SmolVLA path."
        )
    raise RuntimeError(f"Config mode '{config.mode}' is not a local runtime mode.")


def run_lerobot_policy_server(config: PlatformConfig) -> int:
    """Start a real LeRobot async inference policy server from platform config."""
    recorder: JsonlMetricsRecorder | None = None
    try:
        run_dir = _create_configured_run_dir(config, "policy-server")
        metadata = _build_configured_metadata("policy-server", config, run_dir)
        recorder = JsonlMetricsRecorder(run_dir, metadata=metadata)
        _copy_source_config(config, run_dir)
        recorder.record_event(
            MetricEvent(
                EVENT_RECOVERY,
                "config-driven policy server startup configured",
                details={"stage": STAGE_SERVER_STARTUP, "component": "policy_server"},
            )
        )
        state = DashboardState.from_config(config, "policy-server")
        _maybe_launch_dashboard(config, state, recorder)
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
        run_dir = _create_configured_run_dir(config, "robot-client")
        metadata = _build_configured_metadata("robot-client", config, run_dir)
        recorder = JsonlMetricsRecorder(run_dir, metadata=metadata)
        _copy_source_config(config, run_dir)
        print(f"Run directory: {run_dir}")
        print(f"LeRobot robot client -> {config.network.endpoint}")

        client_config = build_lerobot_robot_client_config(config)
        RobotClient, visualize = _load_lerobot_robot_client_api()
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


def run_tcp_teleop_follower_server(config: PlatformConfig) -> int:
    """Start a config-driven TCP teleoperation follower server."""
    recorder: JsonlMetricsRecorder | None = None
    follower = None
    try:
        settings = tcp_teleop_settings(config)
        run_dir = _create_configured_run_dir(config, "tcp-teleop-follower")
        metadata = _build_configured_metadata("tcp-teleop-follower", config, run_dir)
        recorder = JsonlMetricsRecorder(run_dir, metadata=metadata)
        _copy_source_config(config, run_dir)
        state = DashboardState.from_config(config, "tcp-teleop-follower")
        _maybe_launch_dashboard(config, state, recorder)
        print(f"Run directory: {run_dir}")
        print(f"TCP teleop follower listening on {settings.host}:{settings.port}")
        follower = build_teleop_follower_robot(config)
        server = TcpTeleopFollowerServer(
            follower_robot=follower,
            settings=settings,
            recorder=recorder,
            state=state,
        )
        result = server.run()
        recorder.write_summary()
        return result
    except KeyboardInterrupt:
        if recorder is not None:
            recorder.write_summary()
        return 0
    except Exception as exc:
        if recorder is not None:
            record_exception_event(
                recorder,
                stage=STAGE_NETWORK,
                component="tcp_teleop_follower",
                exc=exc,
            )
        raise
    finally:
        if follower is not None:
            _disconnect_best_effort(follower)
        if recorder is not None:
            recorder.close()


def run_tcp_teleop_leader_client(config: PlatformConfig) -> int:
    """Start a config-driven TCP teleoperation leader client."""
    recorder: JsonlMetricsRecorder | None = None
    leader = None
    try:
        settings = tcp_teleop_settings(config)
        run_dir = _create_configured_run_dir(config, "tcp-teleop-leader")
        metadata = _build_configured_metadata("tcp-teleop-leader", config, run_dir)
        recorder = JsonlMetricsRecorder(run_dir, metadata=metadata)
        _copy_source_config(config, run_dir)
        state = DashboardState.from_config(config, "tcp-teleop-leader")
        print(f"Run directory: {run_dir}")
        print(f"TCP teleop leader connecting to {settings.host}:{settings.port}")
        leader = build_teleop_leader_device(config)
        client = TcpTeleopLeaderClient(
            leader_device=leader,
            settings=settings,
            recorder=recorder,
            state=state,
        )
        result = client.run()
        recorder.write_summary()
        return result
    except KeyboardInterrupt:
        if recorder is not None:
            recorder.write_summary()
        return 0
    except Exception as exc:
        if recorder is not None:
            record_exception_event(
                recorder,
                stage=STAGE_NETWORK,
                component="tcp_teleop_leader",
                exc=exc,
            )
        raise
    finally:
        if leader is not None:
            _disconnect_best_effort(leader)
        if recorder is not None:
            recorder.close()


def run_mock_tcp_server(config: PlatformConfig) -> int:
    """Serve one mock TCP observation/action exchange."""
    run_dir = _create_configured_run_dir(config, "mock-server")
    metadata = _build_configured_metadata("mock-server", config, run_dir)
    state = DashboardState.from_config(config, "mock-server")
    with JsonlMetricsRecorder(run_dir, metadata=metadata) as recorder:
        _copy_source_config(config, run_dir)
        _maybe_launch_dashboard(config, state, recorder)
        recorder.record_event(
            MetricEvent(
                EVENT_RECOVERY,
                "mock TCP server waiting for one observation",
                details={"stage": STAGE_NETWORK, "component": "mock_tcp_server"},
            )
        )
        print(f"Run directory: {run_dir}")
        print(f"Mock TCP server listening on {config.network.endpoint}")

        def handle_observation(observation: dict[str, Any]) -> dict[str, Any]:
            state.update_connection("client connected")
            state.update_observation(observation)
            action = mirror_joint_action(observation)
            state.update_action(action)
            return action

        server = TcpServer(
            config.network.server_host,
            config.network.server_port,
            handle_observation,
            timeout_s=config.network.timeout_ms / 1000.0,
            max_packet_size=config.network.max_packet_size_mb * 1024 * 1024,
        )
        start = time.perf_counter()
        server.serve_once()
        latency_ms = (time.perf_counter() - start) * 1000.0
        state.update_latency(latency_ms)
        recorder.record_sample(
            MetricSample(
                LATENCY_MS,
                latency_ms,
                "ms",
                tags={"component": "mock_tcp_server"},
            )
        )
        recorder.write_summary()
    return 0


def run_mock_tcp_client(config: PlatformConfig) -> int:
    """Send one mock observation and receive one mock action."""
    run_dir = _create_configured_run_dir(config, "mock-client")
    metadata = _build_configured_metadata("mock-client", config, run_dir)
    with JsonlMetricsRecorder(run_dir, metadata=metadata) as recorder:
        _copy_source_config(config, run_dir)
        observation = make_observation_message(
            frame_id=1,
            timestamp_ns=time.time_ns(),
            robot_type=config.robot.type,
            joint_positions=_mock_joint_positions(),
        )
        print(f"Run directory: {run_dir}")
        print(f"Mock TCP client connecting to {config.network.endpoint}")
        start = time.perf_counter()
        with TcpClient(
            config.network.server_host,
            config.network.server_port,
            timeout_s=config.network.timeout_ms / 1000.0,
            max_packet_size=config.network.max_packet_size_mb * 1024 * 1024,
        ) as client:
            action = client.request_action(observation)
        recorder.record_sample(
            MetricSample(
                LATENCY_MS,
                (time.perf_counter() - start) * 1000.0,
                "ms",
                tags={"component": "mock_tcp_client"},
            )
        )
        recorder.record_event(
            MetricEvent(
                EVENT_RECOVERY,
                "mock TCP client received action",
                details={"frame_id": str(action.get("frame_id", ""))},
            )
        )
        recorder.write_summary()
    return 0


def run_local_mock_loop(config: PlatformConfig, iterations: int = 5) -> int:
    """Run a local hardware-free observation/action loop for config validation."""
    run_dir = _create_configured_run_dir(config, "local-mock")
    metadata = _build_configured_metadata("local-mock", config, run_dir)
    with JsonlMetricsRecorder(run_dir, metadata=metadata) as recorder:
        _copy_source_config(config, run_dir)
        for frame_id in range(1, iterations + 1):
            start = time.perf_counter()
            _action = dict(_mock_joint_positions())
            recorder.record_sample(
                MetricSample(
                    LATENCY_MS,
                    (time.perf_counter() - start) * 1000.0,
                    "ms",
                    tags={"component": "local_mock", "frame_id": str(frame_id)},
                )
            )
        recorder.record_event(
            MetricEvent(EVENT_RECOVERY, "local mock loop completed", details={"iterations": str(iterations)})
        )
        recorder.write_summary()
    print(f"Run directory: {run_dir}")
    return 0


def _build_configured_metadata(role: str, config: PlatformConfig, run_dir: Path) -> dict[str, object]:
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


def _create_configured_run_dir(config: PlatformConfig, role: str) -> Path:
    return create_run_directory(config.experiment.save_dir, role=role)


def _copy_source_config(config: PlatformConfig, run_dir: Path) -> None:
    if config.source_path is not None and config.source_path.exists():
        shutil.copy2(config.source_path, run_dir / "config.yaml")


def _maybe_launch_dashboard(
    config: PlatformConfig,
    state: DashboardState,
    recorder: JsonlMetricsRecorder,
) -> None:
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


def _disconnect_best_effort(device: object) -> None:
    disconnect = getattr(device, "disconnect", None)
    if callable(disconnect):
        try:
            disconnect()
        except Exception:
            pass


def _mock_joint_positions() -> dict[str, float]:
    return {
        "shoulder_pan.pos": 0.0,
        "shoulder_lift.pos": -0.1,
        "elbow_flex.pos": 0.2,
        "wrist_flex.pos": 0.0,
        "wrist_roll.pos": 0.0,
        "gripper.pos": 0.5,
    }


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
