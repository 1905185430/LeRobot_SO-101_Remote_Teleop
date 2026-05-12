"""Hardware-free mock runtimes."""

from __future__ import annotations

import time
from typing import Any

from ..config.schema import PlatformConfig
from ..network.protocol import make_observation_message
from ..network.tcp_client import TcpClient
from ..network.tcp_server import TcpServer, mirror_joint_action
from ..recording.metrics import EVENT_RECOVERY, LATENCY_MS, MetricEvent, MetricSample
from ..recording.recorder import JsonlMetricsRecorder
from ..reliability import STAGE_NETWORK
from ..webui import DashboardState
from .common import (
    build_configured_metadata,
    copy_source_config,
    create_configured_run_dir,
    maybe_launch_dashboard,
    mock_joint_positions,
)


def run_mock_tcp_server(config: PlatformConfig) -> int:
    """Serve one mock TCP observation/action exchange."""
    run_dir = create_configured_run_dir(config, "mock-server")
    metadata = build_configured_metadata("mock-server", config, run_dir)
    state = DashboardState.from_config(config, "mock-server")
    with JsonlMetricsRecorder(run_dir, metadata=metadata) as recorder:
        copy_source_config(config, run_dir)
        maybe_launch_dashboard(config, state, recorder)
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
    run_dir = create_configured_run_dir(config, "mock-client")
    metadata = build_configured_metadata("mock-client", config, run_dir)
    with JsonlMetricsRecorder(run_dir, metadata=metadata) as recorder:
        copy_source_config(config, run_dir)
        observation = make_observation_message(
            frame_id=1,
            timestamp_ns=time.time_ns(),
            robot_type=config.robot.type,
            joint_positions=mock_joint_positions(),
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
    run_dir = create_configured_run_dir(config, "local-mock")
    metadata = build_configured_metadata("local-mock", config, run_dir)
    with JsonlMetricsRecorder(run_dir, metadata=metadata) as recorder:
        copy_source_config(config, run_dir)
        for frame_id in range(1, iterations + 1):
            start = time.perf_counter()
            _action = dict(mock_joint_positions())
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
