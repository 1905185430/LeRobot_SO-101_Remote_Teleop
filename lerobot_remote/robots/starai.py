"""StarAI arm support through LeRobot-backed modules."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Iterable

from ..config.schema import PlatformConfig

STARAI_FOLLOWER_TYPES = {
    "starai",
    "starai_viola_follower",
    "starai_cello_follower",
    "lerobot_starai_viola",
    "lerobot_robot_viola",
    "lerobot_robot_cello",
}

STARAI_LEADER_TYPES = {
    "starai_violin_leader",
    "lerobot_starai_violin",
    "lerobot_teleoperator_violin",
}


@dataclass(frozen=True)
class StarAILeRobotAdapter:
    """Adapter metadata for StarAI arms routed through LeRobot."""

    robot_id: str
    port: str | None
    robot_type: str
    role: str

    def describe(self) -> dict[str, object]:
        return {
            "robot_id": self.robot_id,
            "port": self.port,
            "robot_type": self.robot_type,
            "role": self.role,
            "backend": "lerobot-starai",
        }


def is_starai_follower_type(robot_type: str | None) -> bool:
    return robot_type in STARAI_FOLLOWER_TYPES


def is_starai_leader_type(teleop_type: str | None) -> bool:
    return teleop_type in STARAI_LEADER_TYPES


def build_starai_follower_config(config: PlatformConfig, cameras: dict[str, object] | None = None) -> object:
    """Build a StarAI follower config object from a platform config."""
    _RobotClass, ConfigClass = _load_starai_follower_api(config.robot.type)
    return _instantiate_config(
        ConfigClass,
        port=config.robot.port,
        robot_id=config.robot.id,
        calibration_dir=config.robot.calibration_dir,
        cameras=cameras,
    )


def build_starai_follower_robot(config: PlatformConfig) -> Any:
    """Build and connect a StarAI follower robot through LeRobot."""
    RobotClass, ConfigClass = _load_starai_follower_api(config.robot.type)
    robot_config = _instantiate_config(
        ConfigClass,
        port=config.robot.port,
        robot_id=config.robot.id,
        calibration_dir=config.robot.calibration_dir,
    )
    robot = RobotClass(robot_config)
    if config.robot.skip_initial_position:
        _disable_initial_position_move(robot)
    robot.connect()
    return robot


def build_starai_leader_device(config: PlatformConfig) -> Any:
    """Build and connect a StarAI leader teleoperator through LeRobot."""
    LeaderClass, ConfigClass = _load_starai_leader_api(config.teleop.type)
    leader_config = _instantiate_config(
        ConfigClass,
        port=config.teleop.port,
        robot_id=config.teleop.id,
        calibration_dir=config.teleop.calibration_dir,
    )
    leader = LeaderClass(leader_config)
    leader.connect()
    return leader


def _load_starai_follower_api(robot_type: str) -> tuple[type, type]:
    module_names = _starai_follower_modules(robot_type)
    class_pairs = (
        ("StaraiViola", "StaraiViolaConfig"),
        ("StaraiCello", "StaraiCelloConfig"),
        ("StarAIRobot", "StarAIRobotConfig"),
        ("StarAIFollower", "StarAIFollowerConfig"),
        ("LerobotRobotViola", "LerobotRobotViolaConfig"),
        ("LerobotRobotCello", "LerobotRobotCelloConfig"),
        ("ViolaRobot", "ViolaRobotConfig"),
        ("CelloRobot", "CelloRobotConfig"),
        ("Robot", "RobotConfig"),
    )
    return _load_class_pair(module_names, class_pairs, "StarAI follower")


def _disable_initial_position_move(robot: Any) -> None:
    """Disable StarAI follower startup pose movement for safer teleoperation startup."""
    move_to_initial_position = getattr(robot, "move_to_initial_position", None)
    if not callable(move_to_initial_position):
        return

    def skip_move_to_initial_position() -> dict[str, object]:
        print("StarAI follower startup initial-position move skipped by config.", flush=True)
        return {}

    setattr(robot, "move_to_initial_position", skip_move_to_initial_position)


def _load_starai_leader_api(teleop_type: str | None) -> tuple[type, type]:
    module_names = _starai_leader_modules(teleop_type)
    class_pairs = (
        ("StaraiViolin", "StaraiViolinConfig"),
        ("StarAILeader", "StarAILeaderConfig"),
        ("StarAITeleoperator", "StarAITeleoperatorConfig"),
        ("LerobotTeleoperatorViolin", "LerobotTeleoperatorViolinConfig"),
        ("ViolinTeleoperator", "ViolinTeleoperatorConfig"),
        ("Leader", "LeaderConfig"),
    )
    return _load_class_pair(module_names, class_pairs, "StarAI leader")


def _starai_follower_modules(robot_type: str) -> tuple[str, ...]:
    normalized = robot_type.replace("-", "_")
    modules = [
        normalized,
        f"{normalized}.config_starai_viola",
        f"{normalized}.config_starai_cello",
        f"{normalized}.starai_viola",
        f"{normalized}.starai_cello",
        f"lerobot.robots.{normalized}",
        f"lerobot.robots.{normalized}.configuration_{normalized}",
        "lerobot_robot_viola",
        "lerobot_robot_viola.config_starai_viola",
        "lerobot_robot_viola.starai_viola",
        "lerobot_robot_cello",
        "lerobot_robot_cello.config_starai_cello",
        "lerobot_robot_cello.starai_cello",
        "lerobot.robots.starai",
        "lerobot.robots.starai.configuration_starai",
        "lerobot.robots.lerobot_robot_viola",
        "lerobot.robots.lerobot_robot_viola.configuration_lerobot_robot_viola",
        "lerobot.robots.lerobot_robot_cello",
        "lerobot.robots.lerobot_robot_cello.configuration_lerobot_robot_cello",
        "lerobot.robots.lerobot_starai_viola",
        "lerobot.robots.lerobot_starai_viola.configuration_lerobot_starai_viola",
    ]
    return tuple(dict.fromkeys(modules))


def _starai_leader_modules(teleop_type: str | None) -> tuple[str, ...]:
    normalized = (teleop_type or "starai_violin_leader").replace("-", "_")
    modules = [
        normalized,
        f"{normalized}.config_starai_violin",
        f"{normalized}.starai_violin",
        f"lerobot.teleoperators.{normalized}",
        f"lerobot.teleoperators.{normalized}.configuration_{normalized}",
        "lerobot_teleoperator_violin",
        "lerobot_teleoperator_violin.config_starai_violin",
        "lerobot_teleoperator_violin.starai_violin",
        "lerobot.teleoperators.starai",
        "lerobot.teleoperators.starai.configuration_starai",
        "lerobot.teleoperators.lerobot_teleoperator_violin",
        "lerobot.teleoperators.lerobot_teleoperator_violin.configuration_lerobot_teleoperator_violin",
        "lerobot.teleoperators.lerobot_starai_violin",
        "lerobot.teleoperators.lerobot_starai_violin.configuration_lerobot_starai_violin",
    ]
    return tuple(dict.fromkeys(modules))


def _load_class_pair(
    module_names: Iterable[str],
    class_pairs: Iterable[tuple[str, str]],
    label: str,
) -> tuple[type, type]:
    import_errors: list[str] = []
    for module_name in module_names:
        try:
            module = import_module(module_name)
        except ImportError as exc:
            import_errors.append(f"{module_name}: {exc}")
            continue
        for runtime_class_name, config_class_name in class_pairs:
            runtime_class = getattr(module, runtime_class_name, None)
            config_class = getattr(module, config_class_name, None)
            if runtime_class is not None and config_class is not None:
                return runtime_class, config_class
    raise RuntimeError(
        f"Failed to import LeRobot {label} classes. Install a LeRobot build with StarAI "
        f"support, or add the matching module/class names. Tried: {', '.join(module_names)}."
    )


def _instantiate_config(
    ConfigClass: type,
    *,
    port: str | None,
    robot_id: str,
    calibration_dir: str | None = None,
    cameras: dict[str, object] | None = None,
) -> object:
    attempts: list[dict[str, object]] = []
    base: dict[str, object] = {"port": port, "id": robot_id}
    if calibration_dir is not None:
        base["calibration_dir"] = Path(calibration_dir)
    if cameras is not None:
        attempts.append({**base, "cameras": cameras})
    attempts.append(base)
    robot_id_base: dict[str, object] = {"port": port, "robot_id": robot_id}
    if calibration_dir is not None:
        robot_id_base["calibration_dir"] = Path(calibration_dir)
    attempts.append(robot_id_base)
    for kwargs in attempts:
        try:
            return ConfigClass(**kwargs)
        except TypeError:
            continue
    return ConfigClass(**base)
