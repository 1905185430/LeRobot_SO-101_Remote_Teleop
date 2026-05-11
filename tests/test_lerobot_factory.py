from __future__ import annotations

import sys
import types
import unittest
from unittest import mock

from so101_remote.config_loader import load_config
from so101_remote.config_schema import ConfigError
from so101_remote.lerobot_factory import (
    build_lerobot_camera_configs,
    build_lerobot_policy_server_config,
    build_lerobot_robot_client_config,
    build_lerobot_robot_config,
    describe_lerobot_runtime,
)


class FakeConfig:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs


def install_fake_lerobot_modules() -> None:
    lerobot_module = types.ModuleType("lerobot")
    async_module = types.ModuleType("lerobot.async_inference")
    configs_module = types.ModuleType("lerobot.async_inference.configs")
    configs_module.PolicyServerConfig = FakeConfig
    configs_module.RobotClientConfig = FakeConfig

    cameras_module = types.ModuleType("lerobot.cameras")
    opencv_module = types.ModuleType("lerobot.cameras.opencv")
    opencv_config_module = types.ModuleType("lerobot.cameras.opencv.configuration_opencv")
    opencv_config_module.OpenCVCameraConfig = FakeConfig

    robots_module = types.ModuleType("lerobot.robots")
    so101_module = types.ModuleType("lerobot.robots.so101_follower")
    so101_module.SO101FollowerConfig = FakeConfig

    patcher = mock.patch.dict(
        sys.modules,
        {
            "lerobot": lerobot_module,
            "lerobot.async_inference": async_module,
            "lerobot.async_inference.configs": configs_module,
            "lerobot.cameras": cameras_module,
            "lerobot.cameras.opencv": opencv_module,
            "lerobot.cameras.opencv.configuration_opencv": opencv_config_module,
            "lerobot.robots": robots_module,
            "lerobot.robots.so101_follower": so101_module,
        },
    )
    patcher.start()


class LeRobotFactoryTests(unittest.TestCase):
    def setUp(self) -> None:
        install_fake_lerobot_modules()
        self.addCleanup(mock.patch.stopall)

    def test_describe_lerobot_runtime_from_config(self) -> None:
        config = load_config("configs/remote_inference_so101_smolvla.yaml")

        description = describe_lerobot_runtime(config)

        self.assertEqual(description["mode"], "remote_inference")
        self.assertEqual(description["robot"]["type"], "so101_follower")
        self.assertEqual(description["policy"]["type"], "smolvla")
        self.assertEqual(description["network"]["endpoint"], "192.168.1.151:9000")

    def test_build_camera_and_robot_configs(self) -> None:
        config = load_config("configs/remote_inference_so101_smolvla.yaml")

        cameras = build_lerobot_camera_configs(config)
        robot = build_lerobot_robot_config(config)

        self.assertEqual(sorted(cameras), ["front", "wrist"])
        self.assertEqual(cameras["front"].kwargs["index_or_path"], 0)
        self.assertEqual(cameras["wrist"].kwargs["fps"], 30)
        self.assertEqual(robot.kwargs["port"], "/dev/ttyACM0")
        self.assertEqual(robot.kwargs["id"], "my_blue_follower_arm")
        self.assertEqual(sorted(robot.kwargs["cameras"]), ["front", "wrist"])

    def test_build_robot_client_config(self) -> None:
        config = load_config("configs/remote_inference_so101_smolvla.yaml")

        client_config = build_lerobot_robot_client_config(config)

        self.assertEqual(client_config.kwargs["server_address"], "192.168.1.151:9000")
        self.assertEqual(client_config.kwargs["policy_type"], "smolvla")
        self.assertEqual(client_config.kwargs["policy_device"], "cuda")
        self.assertEqual(client_config.kwargs["actions_per_chunk"], 30)
        self.assertIsInstance(client_config.kwargs["robot"], FakeConfig)

    def test_build_policy_server_config(self) -> None:
        config = load_config("configs/remote_inference_so101_smolvla.yaml")

        server_config = build_lerobot_policy_server_config(config)

        self.assertEqual(server_config.kwargs, {"host": "192.168.1.151", "port": 9000})

    def test_unsupported_robot_type_is_rejected(self) -> None:
        config = load_config("configs/debug_mock_robot.yaml")

        with self.assertRaisesRegex(ConfigError, "Unsupported robot.type"):
            build_lerobot_robot_config(config)

    def test_unsupported_policy_type_is_rejected(self) -> None:
        config = load_config("configs/debug_mock_robot.yaml")

        with self.assertRaisesRegex(ConfigError, "Unsupported model.type"):
            build_lerobot_policy_server_config(config)


if __name__ == "__main__":
    unittest.main()
