"""Config-driven LeRobot object factories.

These helpers translate `PlatformConfig` into LeRobot config objects while keeping
LeRobot imports lazy so tests and config validation work without hardware deps.
"""

from __future__ import annotations

from importlib import import_module

from .config_schema import ConfigError, PlatformConfig
from .starai import STARAI_FOLLOWER_TYPES, build_starai_follower_config, is_starai_follower_type

SUPPORTED_ROBOT_TYPES = {"so101_follower", *STARAI_FOLLOWER_TYPES}
SUPPORTED_POLICY_TYPES = {"smolvla"}


def describe_lerobot_runtime(config: PlatformConfig) -> dict[str, object]:
    """Return the LeRobot runtime choices implied by a platform config."""
    return {
        "mode": config.mode,
        "robot": {
            "type": config.robot.type,
            "id": config.robot.id,
            "port": config.robot.port,
            "camera_names": sorted(config.camera.cameras),
        },
        "policy": {
            "type": config.model.type,
            "model_path": config.model.model_path,
            "device": config.model.device,
            "dtype": config.model.dtype,
            "action_horizon": config.model.action_horizon,
            "inference_frequency": config.model.inference_frequency,
        },
        "network": {
            "server_host": config.network.server_host,
            "server_port": config.network.server_port,
            "endpoint": config.network.endpoint,
        },
    }


def build_lerobot_camera_configs(config: PlatformConfig) -> dict[str, object]:
    """Build LeRobot OpenCV camera configs from platform config."""
    _ensure_robot_supported(config)
    OpenCVCameraConfig = _load_opencv_camera_config()
    return {
        name: OpenCVCameraConfig(
            index_or_path=camera.index,
            width=camera.width,
            height=camera.height,
            fps=camera.fps,
        )
        for name, camera in config.camera.cameras.items()
    }


def build_lerobot_robot_config(config: PlatformConfig) -> object:
    """Build a LeRobot robot config from platform config."""
    _ensure_robot_supported(config)
    if not config.robot.port:
        raise ConfigError(f"robot.port is required for {config.robot.type}.")
    if is_starai_follower_type(config.robot.type):
        return build_starai_follower_config(config, cameras=build_lerobot_camera_configs(config))
    _OpenCVCameraConfig, SO101FollowerConfig, _RobotClientConfig, _PolicyServerConfig = (
        _load_lerobot_config_api()
    )
    return SO101FollowerConfig(
        port=config.robot.port,
        id=config.robot.id,
        cameras=build_lerobot_camera_configs(config),
    )


def build_lerobot_robot_client_config(config: PlatformConfig) -> object:
    """Build a LeRobot async inference RobotClientConfig from platform config."""
    _ensure_robot_supported(config)
    _ensure_policy_supported(config)
    _OpenCVCameraConfig, _SO101FollowerConfig, RobotClientConfig, _PolicyServerConfig = (
        _load_lerobot_config_api()
    )
    return RobotClientConfig(
        robot=build_lerobot_robot_config(config),
        server_address=config.network.endpoint,
        policy_device=config.model.device,
        policy_type=config.model.type,
        pretrained_name_or_path=config.model.model_path,
        chunk_size_threshold=0.5,
        actions_per_chunk=config.model.action_horizon,
        aggregate_fn_name="weighted_average",
        debug_visualize_queue_size=False,
    )


def build_lerobot_policy_server_config(config: PlatformConfig) -> object:
    """Build a LeRobot async inference PolicyServerConfig from platform config."""
    _ensure_policy_supported(config)
    _OpenCVCameraConfig, _SO101FollowerConfig, _RobotClientConfig, PolicyServerConfig = (
        _load_lerobot_config_api()
    )
    return PolicyServerConfig(host=config.network.server_host, port=config.network.server_port)


def _ensure_robot_supported(config: PlatformConfig) -> None:
    if config.robot.type not in SUPPORTED_ROBOT_TYPES:
        raise ConfigError(
            f"Unsupported robot.type '{config.robot.type}'. "
            f"Expected one of: {', '.join(sorted(SUPPORTED_ROBOT_TYPES))}."
        )


def _ensure_policy_supported(config: PlatformConfig) -> None:
    if config.model.type not in SUPPORTED_POLICY_TYPES:
        raise ConfigError(
            f"Unsupported model.type '{config.model.type}'. "
            f"Expected one of: {', '.join(sorted(SUPPORTED_POLICY_TYPES))}."
        )


def _load_lerobot_config_api() -> tuple[type, type, type, type]:
    """Load LeRobot config classes lazily."""
    try:
        OpenCVCameraConfig = import_module(
            "lerobot.cameras.opencv.configuration_opencv"
        ).OpenCVCameraConfig
        SO101FollowerConfig = _load_so101_follower_config()
        configs_module = import_module("lerobot.async_inference.configs")
        RobotClientConfig = configs_module.RobotClientConfig
        PolicyServerConfig = configs_module.PolicyServerConfig
    except ImportError as exc:
        raise RuntimeError(
            "LeRobot is not available. Install lerobot before building real runtime configs."
        ) from exc

    return OpenCVCameraConfig, SO101FollowerConfig, RobotClientConfig, PolicyServerConfig


def _load_opencv_camera_config() -> type:
    try:
        return import_module("lerobot.cameras.opencv.configuration_opencv").OpenCVCameraConfig
    except ImportError as exc:
        raise RuntimeError(
            "LeRobot OpenCV camera config is not available. Install lerobot before building "
            "real runtime configs."
        ) from exc


def _load_so101_follower_config() -> type:
    module_names = (
        "lerobot.robots.so_follower",
        "lerobot.robots.so101_follower",
        "lerobot.robots.so101_follower.configuration_so101_follower",
    )
    for module_name in module_names:
        try:
            return import_module(module_name).SO101FollowerConfig
        except ImportError:
            continue
    raise ImportError("Could not import SO101FollowerConfig from LeRobot.")
