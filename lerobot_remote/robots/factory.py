"""Robot and teleoperator factory dispatch."""

from __future__ import annotations

from typing import Any

from ..config.schema import PlatformConfig
from .so101 import build_so101_follower_robot, build_so101_leader_device
from .starai import (
    STARAI_FOLLOWER_TYPES,
    STARAI_LEADER_TYPES,
    build_starai_follower_robot,
    build_starai_leader_device,
    is_starai_follower_type,
    is_starai_leader_type,
)

SUPPORTED_TELEOP_FOLLOWER_TYPES = {"so101_follower", *STARAI_FOLLOWER_TYPES}
SUPPORTED_TELEOP_LEADER_TYPES = {"so101_leader", *STARAI_LEADER_TYPES}


def build_teleop_leader_device(config: PlatformConfig) -> Any:
    """Build and connect the configured leader teleoperator."""
    if is_starai_leader_type(config.teleop.type):
        return build_starai_leader_device(config)
    return build_so101_leader_device(config)


def build_teleop_follower_robot(config: PlatformConfig) -> Any:
    """Build and connect the configured follower robot."""
    if is_starai_follower_type(config.robot.type):
        return build_starai_follower_robot(config)
    return build_so101_follower_robot(config)
