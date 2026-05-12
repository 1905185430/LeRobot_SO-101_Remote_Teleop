"""Config-driven runtime dispatch."""

from __future__ import annotations

from ..config.schema import PlatformConfig
from .common import configured_runtime_summary
from .debug_mock import run_local_mock_loop, run_mock_tcp_client, run_mock_tcp_server
from .remote_inference import run_lerobot_policy_server, run_lerobot_robot_client
from .remote_teleop import run_tcp_teleop_follower_server, run_tcp_teleop_leader_client


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
