"""SO-101 LeRobot device builders."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

from ..config.schema import PlatformConfig


def build_so101_leader_device(config: PlatformConfig) -> Any:
    """Build and connect a LeRobot SO-101 leader teleop device."""
    SO101Leader, SO101LeaderConfig = _load_so101_leader_api()
    leader_config = _build_lerobot_device_config(
        SO101LeaderConfig,
        port=config.teleop.port,
        device_id=config.teleop.id,
        calibration_dir=config.teleop.calibration_dir,
    )
    leader = SO101Leader(leader_config)
    leader.connect()
    return leader


def build_so101_follower_robot(config: PlatformConfig) -> Any:
    """Build and connect a LeRobot SO-101 follower robot."""
    SO101Follower, SO101FollowerConfig = _load_so101_follower_api()
    follower_config = _build_lerobot_device_config(
        SO101FollowerConfig,
        port=config.robot.port,
        device_id=config.robot.id,
        calibration_dir=config.robot.calibration_dir,
    )
    follower = SO101Follower(follower_config)
    follower.connect()
    return follower


def _build_lerobot_device_config(
    ConfigClass: type,
    *,
    port: str | None,
    device_id: str,
    calibration_dir: str | None,
) -> object:
    kwargs: dict[str, object] = {"port": port, "id": device_id}
    if calibration_dir is not None:
        kwargs["calibration_dir"] = Path(calibration_dir)
    try:
        return ConfigClass(**kwargs)
    except TypeError:
        kwargs.pop("calibration_dir", None)
        return ConfigClass(**kwargs)


def _load_so101_leader_api() -> tuple[type, type]:
    module_names = (
        "lerobot.teleoperators.so_leader",
        "lerobot.teleoperators.so101_leader",
        "lerobot.teleoperators.so101_leader.configuration_so101_leader",
    )
    for module_name in module_names:
        try:
            module = import_module(module_name)
            return module.SO101Leader, module.SO101LeaderConfig
        except ImportError:
            continue
    raise RuntimeError("Failed to import LeRobot SO101Leader. Install lerobot on the leader machine.")


def _load_so101_follower_api() -> tuple[type, type]:
    module_names = (
        "lerobot.robots.so_follower",
        "lerobot.robots.so101_follower",
        "lerobot.robots.so101_follower.configuration_so101_follower",
    )
    for module_name in module_names:
        try:
            module = import_module(module_name)
            return module.SO101Follower, module.SO101FollowerConfig
        except ImportError:
            continue
    raise RuntimeError("Failed to import LeRobot SO101Follower. Install lerobot on the follower machine.")
