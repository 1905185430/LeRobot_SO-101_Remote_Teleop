from __future__ import annotations

from dataclasses import replace
import socket
import sys
import threading
import time
import types
import unittest
from tempfile import TemporaryDirectory
from unittest import mock

from lerobot_remote.config.loader import load_config
from lerobot_remote.runtime import (
    configured_runtime_summary,
    run_lerobot_policy_server,
    run_lerobot_robot_client,
    run_mock_tcp_client,
    run_mock_tcp_server,
)


class FakeConfig:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs


class FakeRobotClient:
    instances: list[FakeRobotClient] = []

    def __init__(self, config) -> None:
        self.config = config
        self.started = False
        self.stopped = False
        self.received_actions = False
        self.control_task = None
        FakeRobotClient.instances.append(self)

    def start(self) -> bool:
        self.started = True
        return True

    def receive_actions(self) -> None:
        self.received_actions = True

    def control_loop(self, task: str) -> None:
        self.control_task = task

    def stop(self) -> None:
        self.stopped = True


def install_fake_lerobot_modules(served_configs: list[object]) -> None:
    FakeRobotClient.instances.clear()
    lerobot_module = types.ModuleType("lerobot")
    async_module = types.ModuleType("lerobot.async_inference")
    configs_module = types.ModuleType("lerobot.async_inference.configs")
    configs_module.PolicyServerConfig = FakeConfig
    configs_module.RobotClientConfig = FakeConfig

    policy_server_module = types.ModuleType("lerobot.async_inference.policy_server")

    def serve(config) -> None:
        served_configs.append(config)

    policy_server_module.serve = serve

    robot_client_module = types.ModuleType("lerobot.async_inference.robot_client")
    robot_client_module.RobotClient = FakeRobotClient

    helpers_module = types.ModuleType("lerobot.async_inference.helpers")
    helpers_module.visualize_action_queue_size = lambda _queue_size: None

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
            "lerobot.async_inference.policy_server": policy_server_module,
            "lerobot.async_inference.robot_client": robot_client_module,
            "lerobot.async_inference.helpers": helpers_module,
            "lerobot.cameras": cameras_module,
            "lerobot.cameras.opencv": opencv_module,
            "lerobot.cameras.opencv.configuration_opencv": opencv_config_module,
            "lerobot.robots": robots_module,
            "lerobot.robots.so101_follower": so101_module,
        },
    )
    patcher.start()


def with_save_dir(config, save_dir: str):
    return replace(config, experiment=replace(config.experiment, save_dir=save_dir))


def with_endpoint(config, save_dir: str, host: str, port: int):
    return replace(
        with_save_dir(config, save_dir),
        network=replace(config.network, server_host=host, server_port=port, timeout_ms=2000),
    )


def free_local_endpoint() -> tuple[str, int]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    host, port = sock.getsockname()
    sock.close()
    return host, port


class ConfiguredRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.served_configs: list[object] = []
        install_fake_lerobot_modules(self.served_configs)
        self.addCleanup(mock.patch.stopall)

    def test_runtime_summary_includes_lerobot_for_real_path(self) -> None:
        config = load_config("configs/remote_inference/so101_smolvla.yaml")

        summary = configured_runtime_summary("server", config)

        self.assertEqual(summary["role"], "server")
        self.assertEqual(summary["lerobot"]["policy"]["type"], "smolvla")

    def test_lerobot_policy_server_runs_from_config(self) -> None:
        with TemporaryDirectory() as tmpdir:
            config = with_save_dir(load_config("configs/remote_inference/so101_smolvla.yaml"), tmpdir)

            result = run_lerobot_policy_server(config)

        self.assertEqual(result, 0)
        self.assertEqual(len(self.served_configs), 1)
        self.assertEqual(self.served_configs[0].kwargs["host"], "192.168.1.151")

    def test_lerobot_robot_client_runs_from_config(self) -> None:
        with TemporaryDirectory() as tmpdir:
            config = with_save_dir(load_config("configs/remote_inference/so101_smolvla.yaml"), tmpdir)

            result = run_lerobot_robot_client(config)

        self.assertEqual(result, 0)
        self.assertEqual(len(FakeRobotClient.instances), 1)
        instance = FakeRobotClient.instances[0]
        self.assertTrue(instance.started)
        self.assertEqual(instance.control_task, "pick_place_cube")
        self.assertEqual(instance.config.kwargs["server_address"], "192.168.1.151:9000")

    def test_mock_tcp_client_server_roundtrip_from_config(self) -> None:
        host, port = free_local_endpoint()
        with TemporaryDirectory() as tmpdir:
            config = with_endpoint(load_config("configs/debug/debug_mock_robot.yaml"), tmpdir, host, port)
            errors: list[BaseException] = []

            def serve() -> None:
                try:
                    run_mock_tcp_server(config)
                except BaseException as exc:  # pragma: no cover - surfaced below
                    errors.append(exc)

            thread = threading.Thread(target=serve, daemon=True)
            thread.start()
            time.sleep(0.02)

            result = run_mock_tcp_client(config)
            thread.join(timeout=2.0)

        self.assertEqual(result, 0)
        self.assertFalse(errors)
        self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main()
