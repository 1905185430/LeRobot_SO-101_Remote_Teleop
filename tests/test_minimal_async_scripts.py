from __future__ import annotations

import json
import sys
import tempfile
import types
import unittest
from unittest import mock

import robot_client
import so101_remote.client as robot_client_runtime
import so101_remote.server as policy_server


class FakePolicyServerConfig:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs


class FakeRobotClientConfig:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs


class FakeOpenCVCameraConfig:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs


class FakeSO101FollowerConfig:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs


class FakeRobotClient:
    def __init__(self, config) -> None:
        self.config = config
        self.action_queue_size = [1, 2, 3]
        self.started = False
        self.received = False
        self.control_task = None
        self.stopped = False

    def start(self) -> bool:
        self.started = True
        return True

    def receive_actions(self) -> None:
        self.received = True

    def control_loop(self, task: str) -> None:
        self.control_task = task

    def stop(self) -> None:
        self.stopped = True


class FakeBoomRobotClient(FakeRobotClient):
    def control_loop(self, task: str) -> None:
        raise RuntimeError("client boom")


class FakeThread:
    def __init__(self, target, daemon: bool) -> None:
        self.target = target
        self.daemon = daemon
        self.started = False
        self.joined = False

    def start(self) -> None:
        self.started = True
        self.target()

    def join(self) -> None:
        self.joined = True


def install_fake_lerobot_modules() -> None:
    # The real LeRobot package is not installed in CI/local tests here, so we stub only the
    # modules touched by the two minimal entry scripts.
    lerobot_module = types.ModuleType("lerobot")
    async_module = types.ModuleType("lerobot.async_inference")
    configs_module = types.ModuleType("lerobot.async_inference.configs")
    configs_module.PolicyServerConfig = FakePolicyServerConfig
    configs_module.RobotClientConfig = FakeRobotClientConfig

    policy_server_module = types.ModuleType("lerobot.async_inference.policy_server")
    policy_server_module.serve = mock.Mock()

    robot_client_module = types.ModuleType("lerobot.async_inference.robot_client")
    robot_client_module.RobotClient = FakeRobotClient

    helpers_module = types.ModuleType("lerobot.async_inference.helpers")
    helpers_module.visualize_action_queue_size = mock.Mock()

    cameras_module = types.ModuleType("lerobot.cameras")
    opencv_module = types.ModuleType("lerobot.cameras.opencv")
    opencv_config_module = types.ModuleType("lerobot.cameras.opencv.configuration_opencv")
    opencv_config_module.OpenCVCameraConfig = FakeOpenCVCameraConfig

    robots_module = types.ModuleType("lerobot.robots")
    so101_module = types.ModuleType("lerobot.robots.so101_follower")
    so101_module.SO101FollowerConfig = FakeSO101FollowerConfig

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


class MinimalAsyncScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module_patcher = install_fake_lerobot_modules()
        self.addCleanup(mock.patch.stopall)

    def test_policy_server_builds_official_config(self) -> None:
        config = policy_server.build_server_config()
        self.assertIsInstance(config, FakePolicyServerConfig)
        self.assertEqual(config.kwargs, {"host": policy_server.HOST, "port": policy_server.PORT})

    def test_policy_server_settings_are_resolved(self) -> None:
        self.assertEqual(
            policy_server.server_settings(),
            {
                "host": policy_server.HOST,
                "port": policy_server.PORT,
                "endpoint": f"{policy_server.HOST}:{policy_server.PORT}",
            },
        )

    def test_policy_server_metadata_includes_resolved_settings(self) -> None:
        metadata = policy_server.build_server_metadata("/tmp/server-run")

        self.assertEqual(metadata["role"], "policy-server")
        self.assertEqual(metadata["server"]["endpoint"], f"{policy_server.HOST}:{policy_server.PORT}")
        self.assertEqual(metadata["policy"]["type"], "smolvla")
        self.assertEqual(metadata["extra"]["resolved_settings"]["port"], policy_server.PORT)

    def test_top_level_wrappers_export_expected_helpers(self) -> None:
        self.assertTrue(callable(policy_server.build_server_config))
        self.assertTrue(callable(policy_server.main))
        self.assertEqual(robot_client.SERVER_ADDRESS, robot_client_runtime.SERVER_ADDRESS)
        self.assertEqual(robot_client.ROBOT_PORT, robot_client_runtime.ROBOT_PORT)
        self.assertEqual(robot_client.ROBOT_ID, robot_client_runtime.ROBOT_ID)
        self.assertEqual(robot_client.CAMERAS, robot_client_runtime.CAMERAS)
        self.assertEqual(robot_client.TASK, robot_client_runtime.TASK)
        self.assertEqual(robot_client.POLICY_TYPE, robot_client_runtime.POLICY_TYPE)
        self.assertEqual(
            robot_client.PRETRAINED_NAME_OR_PATH,
            robot_client_runtime.PRETRAINED_NAME_OR_PATH,
        )
        self.assertEqual(robot_client.POLICY_DEVICE, robot_client_runtime.POLICY_DEVICE)
        self.assertEqual(robot_client.ACTIONS_PER_CHUNK, robot_client_runtime.ACTIONS_PER_CHUNK)
        self.assertEqual(
            robot_client.CHUNK_SIZE_THRESHOLD,
            robot_client_runtime.CHUNK_SIZE_THRESHOLD,
        )
        self.assertEqual(robot_client.AGGREGATE_FN_NAME, robot_client_runtime.AGGREGATE_FN_NAME)
        self.assertEqual(
            robot_client.DEBUG_VISUALIZE_QUEUE_SIZE,
            robot_client_runtime.DEBUG_VISUALIZE_QUEUE_SIZE,
        )
        self.assertTrue(callable(robot_client.build_camera_configs))
        self.assertTrue(callable(robot_client.build_robot_config))
        self.assertTrue(callable(robot_client.build_client_config))
        self.assertTrue(callable(robot_client.main))

    def test_policy_server_main_calls_serve(self) -> None:
        serve = sys.modules["lerobot.async_inference.policy_server"].serve
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.object(policy_server, "create_run_directory", return_value=tmpdir):
                exit_code = policy_server.main()
            self.assertEqual(exit_code, 0)
            self.assertTrue((policy_server.Path(tmpdir) / "summary.md").exists())
            serve.assert_called_once()
            called_config = serve.call_args.args[0]
            self.assertEqual(called_config.kwargs["host"], policy_server.HOST)
            self.assertEqual(called_config.kwargs["port"], policy_server.PORT)

    def test_policy_server_runtime_writes_metadata(self) -> None:
        serve = sys.modules["lerobot.async_inference.policy_server"].serve
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = policy_server.Path(tmpdir)
            with mock.patch.object(policy_server, "create_run_directory", return_value=run_dir):
                exit_code = policy_server.main()

            self.assertEqual(exit_code, 0)
            serve.assert_called_once()
            metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
            events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
            self.assertEqual(metadata["role"], "policy-server")
            self.assertEqual(metadata["server"]["endpoint"], f"{policy_server.HOST}:{policy_server.PORT}")
            self.assertTrue((run_dir / "metadata.json").exists())
            self.assertTrue((run_dir / "events.jsonl").exists())
            self.assertTrue((run_dir / "summary.md").exists())
            self.assertIn('"event_type": "recovery"', events)

    def test_policy_server_runtime_records_exception_and_reraises(self) -> None:
        serve = sys.modules["lerobot.async_inference.policy_server"].serve
        serve.side_effect = RuntimeError("server boom")

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = policy_server.Path(tmpdir)
            with mock.patch.object(policy_server, "create_run_directory", return_value=run_dir):
                with self.assertRaisesRegex(RuntimeError, "server boom"):
                    policy_server.main()

            events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
            self.assertIn('"event_type": "exception"', events)
            self.assertIn("server boom", events)

    def test_robot_client_builds_expected_config(self) -> None:
        config = robot_client.build_client_config()
        robot_cfg = config.kwargs["robot"]
        self.assertIsInstance(config, FakeRobotClientConfig)
        self.assertEqual(config.kwargs["server_address"], robot_client.SERVER_ADDRESS)
        self.assertEqual(config.kwargs["policy_type"], robot_client.POLICY_TYPE)
        self.assertEqual(config.kwargs["actions_per_chunk"], robot_client.ACTIONS_PER_CHUNK)
        self.assertEqual(robot_cfg.kwargs["port"], robot_client.ROBOT_PORT)
        self.assertEqual(robot_cfg.kwargs["id"], robot_client.ROBOT_ID)
        self.assertIn("front", robot_cfg.kwargs["cameras"])

    def test_robot_client_settings_are_resolved(self) -> None:
        settings = robot_client.client_settings()

        self.assertEqual(
            set(settings),
            {
                "server_address",
                "robot_port",
                "robot_id",
                "cameras",
                "task",
                "policy_type",
                "pretrained_name_or_path",
                "policy_device",
                "actions_per_chunk",
                "chunk_size_threshold",
                "aggregate_fn_name",
                "debug_visualize_queue_size",
            },
        )
        self.assertEqual(settings["server_address"], robot_client.SERVER_ADDRESS)
        self.assertEqual(settings["robot_id"], robot_client.ROBOT_ID)
        self.assertEqual(settings["actions_per_chunk"], robot_client.ACTIONS_PER_CHUNK)

    def test_robot_client_metadata_includes_resolved_settings(self) -> None:
        metadata = robot_client.build_client_metadata("/tmp/client-run")

        self.assertEqual(metadata["role"], "robot-client")
        self.assertEqual(metadata["robot"]["id"], robot_client.ROBOT_ID)
        self.assertEqual(metadata["server"]["address"], robot_client.SERVER_ADDRESS)
        self.assertEqual(metadata["policy"]["type"], robot_client.POLICY_TYPE)
        self.assertEqual(
            metadata["extra"]["resolved_settings"]["actions_per_chunk"],
            robot_client.ACTIONS_PER_CHUNK,
        )

    def test_robot_client_main_starts_and_runs_control_loop(self) -> None:
        fake_thread = mock.Mock(side_effect=FakeThread)
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = robot_client_runtime.Path(tmpdir)
            with (
                mock.patch.object(robot_client_runtime, "create_run_directory", return_value=run_dir),
                mock.patch.object(robot_client.threading, "Thread", fake_thread),
            ):
                exit_code = robot_client.main()

        self.assertEqual(exit_code, 0)
        constructed_client = fake_thread.call_args.kwargs["target"].__self__
        self.assertTrue(constructed_client.started)
        self.assertTrue(constructed_client.received)
        self.assertEqual(constructed_client.control_task, robot_client.TASK)

    def test_robot_client_runtime_writes_metadata(self) -> None:
        fake_thread = mock.Mock(side_effect=FakeThread)

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = robot_client_runtime.Path(tmpdir)
            with (
                mock.patch.object(robot_client_runtime, "create_run_directory", return_value=run_dir),
                mock.patch.object(robot_client.threading, "Thread", fake_thread),
            ):
                exit_code = robot_client.main()

            self.assertEqual(exit_code, 0)
            metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
            events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
            self.assertEqual(metadata["role"], "robot-client")
            self.assertEqual(metadata["robot"]["id"], robot_client.ROBOT_ID)
            self.assertEqual(metadata["server"]["address"], robot_client.SERVER_ADDRESS)
            self.assertTrue((run_dir / "metadata.json").exists())
            self.assertTrue((run_dir / "events.jsonl").exists())
            self.assertTrue((run_dir / "summary.md").exists())
            self.assertIn('"event_type": "recovery"', events)

    def test_robot_client_runtime_records_exception_and_reraises(self) -> None:
        sys.modules["lerobot.async_inference.robot_client"].RobotClient = FakeBoomRobotClient
        fake_thread = mock.Mock(side_effect=FakeThread)

        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = robot_client_runtime.Path(tmpdir)
            with (
                mock.patch.object(robot_client_runtime, "create_run_directory", return_value=run_dir),
                mock.patch.object(robot_client.threading, "Thread", fake_thread),
            ):
                with self.assertRaisesRegex(RuntimeError, "client boom"):
                    robot_client.main()

            events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
            self.assertIn('"event_type": "exception"', events)
            self.assertIn("client boom", events)
