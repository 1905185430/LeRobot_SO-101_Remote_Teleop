from __future__ import annotations

from pathlib import Path
import sys
import types
import unittest
from unittest import mock

from so101_remote.config_loader import load_config
from so101_remote.lerobot_factory import build_lerobot_robot_config
from so101_remote.starai import (
    StarAILeRobotAdapter,
    build_starai_follower_robot,
    build_starai_leader_device,
    is_starai_follower_type,
    is_starai_leader_type,
)
from so101_remote.teleop_tcp import normalize_teleop_action, tcp_teleop_settings


class FakeConfig:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs


class FakeRobot:
    def __init__(self, config) -> None:
        self.config = config
        self.connected = False
        self.moved_to_initial_position = False

    def connect(self) -> None:
        self.move_to_initial_position()
        self.connected = True

    def move_to_initial_position(self) -> dict[str, object]:
        self.moved_to_initial_position = True
        return {}


class FakeLeader(FakeRobot):
    pass


def install_fake_starai_modules() -> None:
    lerobot_module = types.ModuleType("lerobot")
    robots_module = types.ModuleType("lerobot.robots")
    cameras_module = types.ModuleType("lerobot.cameras")
    opencv_module = types.ModuleType("lerobot.cameras.opencv")
    opencv_config_module = types.ModuleType("lerobot.cameras.opencv.configuration_opencv")
    opencv_config_module.OpenCVCameraConfig = FakeConfig

    starai_robot_module = types.ModuleType("lerobot_robot_viola")
    starai_robot_module.StaraiViola = FakeRobot
    starai_robot_module.StaraiViolaConfig = FakeConfig

    teleoperators_module = types.ModuleType("lerobot.teleoperators")
    starai_leader_module = types.ModuleType("lerobot_teleoperator_violin")
    starai_leader_module.StaraiViolin = FakeLeader
    starai_leader_module.StaraiViolinConfig = FakeConfig

    patcher = mock.patch.dict(
        sys.modules,
        {
            "lerobot": lerobot_module,
            "lerobot.robots": robots_module,
            "lerobot_robot_viola": starai_robot_module,
            "lerobot.teleoperators": teleoperators_module,
            "lerobot_teleoperator_violin": starai_leader_module,
            "lerobot.cameras": cameras_module,
            "lerobot.cameras.opencv": opencv_module,
            "lerobot.cameras.opencv.configuration_opencv": opencv_config_module,
        },
    )
    patcher.start()


class StarAITests(unittest.TestCase):
    def setUp(self) -> None:
        install_fake_starai_modules()
        self.addCleanup(mock.patch.stopall)

    def test_starai_adapter_describes_lerobot_backend(self) -> None:
        adapter = StarAILeRobotAdapter(
            robot_id="my_starai_viola_follower",
            port="/dev/ttyUSB1",
            robot_type="lerobot_robot_viola",
            role="follower",
        )

        self.assertEqual(adapter.describe()["backend"], "lerobot-starai")
        self.assertEqual(adapter.describe()["robot_type"], "lerobot_robot_viola")

    def test_starai_type_helpers(self) -> None:
        self.assertTrue(is_starai_follower_type("lerobot_robot_viola"))
        self.assertTrue(is_starai_follower_type("starai_cello_follower"))
        self.assertTrue(is_starai_leader_type("lerobot_teleoperator_violin"))
        self.assertTrue(is_starai_leader_type("starai_violin_leader"))

    def test_starai_remote_teleop_config_is_supported(self) -> None:
        config = load_config("configs/teleop/remote_starai_tcp.yaml")

        settings = tcp_teleop_settings(config)

        self.assertEqual(settings.leader_id, "my_awesome_staraiviolin_arm")
        self.assertEqual(settings.follower_id, "my_awesome_staraiviola_arm")

    def test_build_starai_follower_and_leader_devices(self) -> None:
        config = load_config("configs/teleop/remote_starai_tcp.yaml")

        follower = build_starai_follower_robot(config)
        leader = build_starai_leader_device(config)

        self.assertTrue(follower.connected)
        self.assertTrue(leader.connected)
        self.assertEqual(follower.config.kwargs["port"], "/dev/ttyUSB1")
        self.assertEqual(leader.config.kwargs["id"], "my_awesome_staraiviolin_arm")
        self.assertFalse(follower.moved_to_initial_position)

    def test_build_starai_follower_can_skip_initial_position_move(self) -> None:
        config = load_config("configs/teleop/local_starai_tcp.yaml")

        follower = build_starai_follower_robot(config)

        self.assertTrue(follower.connected)
        self.assertFalse(follower.moved_to_initial_position)
        self.assertEqual(
            follower.config.kwargs["calibration_dir"],
            Path("calibrations/robots/starai_viola"),
        )

    def test_build_starai_leader_uses_configured_calibration_dir(self) -> None:
        config = load_config("configs/teleop/local_starai_tcp.yaml")

        leader = build_starai_leader_device(config)

        self.assertEqual(
            leader.config.kwargs["calibration_dir"],
            Path("calibrations/teleoperators/starai_violin"),
        )

    def test_lerobot_factory_builds_starai_robot_config(self) -> None:
        config = load_config("configs/teleop/remote_starai_tcp.yaml")

        robot_config = build_lerobot_robot_config(config)

        self.assertEqual(robot_config.kwargs["port"], "/dev/ttyUSB1")
        self.assertEqual(robot_config.kwargs["id"], "my_awesome_staraiviola_arm")

    def test_normalize_teleop_action_accepts_starai_dict_keys(self) -> None:
        action = {"joint_1.pos": 1, "joint_2.pos": "2.5", "gripper.pos": 0}

        self.assertEqual(
            normalize_teleop_action(action),
            {"joint_1.pos": 1.0, "joint_2.pos": 2.5, "gripper.pos": 0.0},
        )


if __name__ == "__main__":
    unittest.main()
