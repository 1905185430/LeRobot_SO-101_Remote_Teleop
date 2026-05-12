"""TCP teleoperation settings."""

from __future__ import annotations

from dataclasses import dataclass

from ..config.schema import ConfigError, PlatformConfig
from ..robots.factory import SUPPORTED_TELEOP_FOLLOWER_TYPES, SUPPORTED_TELEOP_LEADER_TYPES


@dataclass(frozen=True)
class TcpTeleopSettings:
    """Resolved TCP teleoperation settings."""

    host: str
    port: int
    timeout_s: float
    max_packet_size: int
    send_hz: float
    control_hz: float
    leader_id: str
    follower_id: str
    hold_last_action_on_timeout: bool
    max_action_delta: float
    max_first_action_delta: float
    action_min: float
    action_max: float
    require_action_keys_match: bool
    print_leader_actions: bool
    print_action_interval: int


def tcp_teleop_settings(config: PlatformConfig) -> TcpTeleopSettings:
    """Build validated TCP teleoperation settings from platform config."""
    if config.mode != "remote_teleoperation":
        raise ConfigError("TCP teleoperation requires experiment.mode=remote_teleoperation.")
    if not config.teleop.enabled:
        raise ConfigError("TCP teleoperation requires teleop.enabled=true.")
    if config.teleop.type not in SUPPORTED_TELEOP_LEADER_TYPES:
        raise ConfigError(
            "TCP teleoperation currently supports teleop.type one of: "
            f"{', '.join(sorted(SUPPORTED_TELEOP_LEADER_TYPES))}."
        )
    if config.robot.type not in SUPPORTED_TELEOP_FOLLOWER_TYPES:
        raise ConfigError(
            "TCP teleoperation currently supports robot.type one of: "
            f"{', '.join(sorted(SUPPORTED_TELEOP_FOLLOWER_TYPES))}."
        )
    if not config.robot.port:
        raise ConfigError("TCP teleoperation server requires robot.port for the follower.")
    if not config.teleop.port:
        raise ConfigError("TCP teleoperation client requires teleop.port for the leader.")

    return TcpTeleopSettings(
        host=config.network.server_host,
        port=config.network.server_port,
        timeout_s=config.network.timeout_ms / 1000.0,
        max_packet_size=config.network.max_packet_size_mb * 1024 * 1024,
        send_hz=config.runtime.action_send_frequency,
        control_hz=config.runtime.control_frequency,
        leader_id=config.teleop.id,
        follower_id=config.robot.id,
        hold_last_action_on_timeout=config.runtime.hold_last_action_on_timeout,
        max_action_delta=config.safety.max_action_delta,
        max_first_action_delta=config.safety.max_first_action_delta,
        action_min=config.safety.action_min,
        action_max=config.safety.action_max,
        require_action_keys_match=config.safety.require_action_keys_match,
        print_leader_actions=config.logging.print_leader_actions,
        print_action_interval=config.logging.print_action_interval,
    )
