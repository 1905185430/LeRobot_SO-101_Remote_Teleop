"""TCP remote teleoperation runtimes."""

from __future__ import annotations

from ..config.schema import PlatformConfig
from ..recording.recorder import JsonlMetricsRecorder
from ..reliability import STAGE_NETWORK, record_exception_event
from ..robots import build_teleop_follower_robot, build_teleop_leader_device
from ..teleop import TcpTeleopFollowerServer, TcpTeleopLeaderClient, tcp_teleop_settings
from ..webui import DashboardState
from .common import (
    build_configured_metadata,
    copy_source_config,
    create_configured_run_dir,
    disconnect_best_effort,
    maybe_launch_dashboard,
)


def run_tcp_teleop_follower_server(config: PlatformConfig) -> int:
    """Start a config-driven TCP teleoperation follower server."""
    recorder: JsonlMetricsRecorder | None = None
    follower = None
    try:
        settings = tcp_teleop_settings(config)
        run_dir = create_configured_run_dir(config, "tcp-teleop-follower")
        metadata = build_configured_metadata("tcp-teleop-follower", config, run_dir)
        recorder = JsonlMetricsRecorder(run_dir, metadata=metadata)
        copy_source_config(config, run_dir)
        state = DashboardState.from_config(config, "tcp-teleop-follower")
        maybe_launch_dashboard(config, state, recorder)
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
            disconnect_best_effort(follower)
        if recorder is not None:
            recorder.close()


def run_tcp_teleop_leader_client(config: PlatformConfig) -> int:
    """Start a config-driven TCP teleoperation leader client."""
    recorder: JsonlMetricsRecorder | None = None
    leader = None
    try:
        settings = tcp_teleop_settings(config)
        run_dir = create_configured_run_dir(config, "tcp-teleop-leader")
        metadata = build_configured_metadata("tcp-teleop-leader", config, run_dir)
        recorder = JsonlMetricsRecorder(run_dir, metadata=metadata)
        copy_source_config(config, run_dir)
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
            disconnect_best_effort(leader)
        if recorder is not None:
            recorder.close()
