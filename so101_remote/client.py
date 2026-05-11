"""LeRobot async inference robot client runtime helpers."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
import threading

from .config import (
    ACTIONS_PER_CHUNK,
    AGGREGATE_FN_NAME,
    CAMERAS,
    CHUNK_SIZE_THRESHOLD,
    DEBUG_VISUALIZE_QUEUE_SIZE,
    POLICY_DEVICE,
    POLICY_TYPE,
    PRETRAINED_NAME_OR_PATH,
    ROBOT_ID,
    ROBOT_PORT,
    SERVER_ADDRESS,
    TASK,
)
from .recorder import build_run_metadata


def client_settings() -> dict[str, object]:
    """Return resolved robot client settings for logs and metadata."""
    return {
        "server_address": SERVER_ADDRESS,
        "robot_port": ROBOT_PORT,
        "robot_id": ROBOT_ID,
        "cameras": CAMERAS,
        "task": TASK,
        "policy_type": POLICY_TYPE,
        "pretrained_name_or_path": PRETRAINED_NAME_OR_PATH,
        "policy_device": POLICY_DEVICE,
        "actions_per_chunk": ACTIONS_PER_CHUNK,
        "chunk_size_threshold": CHUNK_SIZE_THRESHOLD,
        "aggregate_fn_name": AGGREGATE_FN_NAME,
        "debug_visualize_queue_size": DEBUG_VISUALIZE_QUEUE_SIZE,
    }


def build_client_metadata(run_dir: str | Path) -> dict[str, object]:
    """Build reproducibility metadata for a robot client run."""
    return build_run_metadata(
        role="robot-client",
        server={"address": SERVER_ADDRESS},
        robot={"id": ROBOT_ID, "port": ROBOT_PORT, "cameras": CAMERAS},
        policy={
            "type": POLICY_TYPE,
            "pretrained_name_or_path": PRETRAINED_NAME_OR_PATH,
            "device": POLICY_DEVICE,
        },
        extra={"resolved_settings": client_settings(), "run_dir": str(run_dir)},
    )


def build_camera_configs():
    """Build OpenCV camera config objects from CAMERAS."""
    OpenCVCameraConfig, *_rest = _load_client_api()
    return {
        name: OpenCVCameraConfig(
            index_or_path=camera["index_or_path"],
            width=camera["width"],
            height=camera["height"],
            fps=camera["fps"],
        )
        for name, camera in CAMERAS.items()
    }


def build_robot_config():
    """Build the SO-101 follower robot config."""
    _OpenCVCameraConfig, SO101FollowerConfig, *_rest = _load_client_api()
    return SO101FollowerConfig(
        port=ROBOT_PORT,
        id=ROBOT_ID,
        cameras=build_camera_configs(),
    )


def build_client_config():
    """Build the official LeRobot robot client config object."""
    _OpenCVCameraConfig, _SO101FollowerConfig, RobotClientConfig, _RobotClient, _visualize = (
        _load_client_api()
    )
    return RobotClientConfig(
        robot=build_robot_config(),
        server_address=SERVER_ADDRESS,
        policy_device=POLICY_DEVICE,
        policy_type=POLICY_TYPE,
        pretrained_name_or_path=PRETRAINED_NAME_OR_PATH,
        chunk_size_threshold=CHUNK_SIZE_THRESHOLD,
        actions_per_chunk=ACTIONS_PER_CHUNK,
        aggregate_fn_name=AGGREGATE_FN_NAME,
        debug_visualize_queue_size=DEBUG_VISUALIZE_QUEUE_SIZE,
    )


def main() -> int:
    """Start the LeRobot async inference robot client."""
    _OpenCVCameraConfig, _SO101FollowerConfig, _RobotClientConfig, RobotClient, visualize = (
        _load_client_api()
    )
    client = RobotClient(build_client_config())

    if not client.start():
        return 1

    action_receiver_thread = threading.Thread(target=client.receive_actions, daemon=True)
    action_receiver_thread.start()

    try:
        client.control_loop(TASK)
    except KeyboardInterrupt:
        client.stop()
        action_receiver_thread.join()
        if DEBUG_VISUALIZE_QUEUE_SIZE:
            visualize(client.action_queue_size)
    return 0


def _load_client_api():
    """Load LeRobot client APIs lazily so imports remain test-friendly."""
    try:
        RobotClientConfig = import_module(
            "lerobot.async_inference.configs"
        ).RobotClientConfig
        visualize_action_queue_size = import_module(
            "lerobot.async_inference.helpers"
        ).visualize_action_queue_size
        RobotClient = import_module("lerobot.async_inference.robot_client").RobotClient
        OpenCVCameraConfig = import_module(
            "lerobot.cameras.opencv.configuration_opencv"
        ).OpenCVCameraConfig
        SO101FollowerConfig = _load_so101_follower_config()
    except ImportError as exc:
        raise RuntimeError(
            "LeRobot async inference is not available. Install lerobot on this machine "
            "before running robot_client.py."
        ) from exc

    return (
        OpenCVCameraConfig,
        SO101FollowerConfig,
        RobotClientConfig,
        RobotClient,
        visualize_action_queue_size,
    )


def _load_so101_follower_config():
    """Support SO-101 follower config module paths used by different LeRobot versions."""
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
