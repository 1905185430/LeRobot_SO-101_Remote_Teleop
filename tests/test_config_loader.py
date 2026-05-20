from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from lerobot_remote.config.loader import load_config, parse_simple_yaml
from lerobot_remote.config.schema import ConfigError, platform_config_from_mapping


ROOT = Path(__file__).resolve().parents[1]


class ConfigLoaderTests(unittest.TestCase):
    def test_load_remote_inference_config(self) -> None:
        config = load_config(ROOT / "configs" / "remote_inference" / "so101_smolvla.yaml")

        self.assertEqual(config.mode, "remote_inference")
        self.assertEqual(config.robot.type, "so101_follower")
        self.assertEqual(config.model.type, "smolvla")
        self.assertEqual(config.network.protocol, "tcp")
        self.assertEqual(config.network.endpoint, "192.168.1.151:9000")
        self.assertEqual(sorted(config.camera.cameras), ["front", "wrist"])
        self.assertTrue(config.webui.enabled)

    def test_load_local_inference_config(self) -> None:
        config = load_config(ROOT / "configs" / "local_inference" / "so101_smolvla.yaml")

        self.assertEqual(config.mode, "local_inference")
        self.assertEqual(config.network.server_host, "127.0.0.1")
        self.assertFalse(config.webui.enabled)
        self.assertEqual(config.safety.max_action_delta, 2.0)

    def test_load_local_starai_teleop_safety_config(self) -> None:
        config = load_config(ROOT / "configs" / "teleop" / "local_starai_tcp.yaml")

        self.assertEqual(config.safety.max_action_delta, 1.0)
        self.assertEqual(config.safety.max_first_action_delta, 12.0)
        self.assertEqual(config.safety.action_min, -100)
        self.assertEqual(config.safety.action_max, 100)
        self.assertTrue(config.safety.require_action_keys_match)
        self.assertTrue(config.robot.skip_initial_position)
        self.assertEqual(config.robot.calibration_dir, "calibrations/robots/starai_viola")
        self.assertEqual(config.teleop.calibration_dir, "calibrations/teleoperators/starai_violin")
        self.assertTrue(config.logging.print_leader_actions)
        self.assertEqual(config.logging.print_action_interval, 10)

    def test_load_local_so101_teleop_config(self) -> None:
        config = load_config(ROOT / "configs" / "teleop" / "local_so101_tcp.yaml")

        self.assertEqual(config.experiment.name, "so101_local_teleop_tcp")
        self.assertEqual(config.mode, "remote_teleoperation")
        self.assertEqual(config.network.endpoint, "127.0.0.1:9011")
        self.assertEqual(config.robot.type, "so101_follower")
        self.assertEqual(config.robot.port, "/dev/ttyACM1")
        self.assertEqual(config.robot.id, "follower_arm")
        self.assertEqual(config.robot.calibration_dir, "calibrations/robots/so_follower")
        self.assertEqual(config.teleop.type, "so101_leader")
        self.assertEqual(config.teleop.port, "/dev/ttyACM0")
        self.assertEqual(config.teleop.id, "leader_arm")
        self.assertEqual(config.teleop.calibration_dir, "calibrations/teleoperators/so_leader")
        self.assertEqual(config.safety.action_min, -180)
        self.assertEqual(config.safety.action_max, 180)

    def test_load_local_so101_dataset_replay_config(self) -> None:
        config = load_config(ROOT / "configs" / "replay" / "local_so101_tcp_dataset.yaml")

        self.assertEqual(config.experiment.name, "so101_local_tcp_dataset_replay")
        self.assertEqual(config.mode, "remote_teleoperation")
        self.assertEqual(config.network.endpoint, "127.0.0.1:9012")
        self.assertEqual(config.dataset.path, "/tmp/lerobot/so101_dataset")
        self.assertEqual(config.dataset.episode, 0)
        self.assertEqual(config.dataset.start_frame, 0)
        self.assertEqual(config.dataset.end_frame, -1)
        self.assertEqual(config.dataset.timing, "fixed_hz")
        self.assertEqual(config.dataset.replay_frequency, 50.0)
        self.assertEqual(config.robot.type, "so101_follower")
        self.assertEqual(config.teleop.type, "so101_leader")

    def test_remote_teleoperation_requires_enabled_teleop(self) -> None:
        data = {
            "experiment": {"name": "bad", "mode": "remote_teleoperation"},
            "robot": {"type": "so101_follower"},
            "model": {"type": "mock"},
            "teleop": {"enabled": False},
        }

        with self.assertRaisesRegex(ConfigError, "teleop.enabled=true"):
            platform_config_from_mapping(data)

    def test_invalid_network_protocol_is_rejected(self) -> None:
        data = {
            "experiment": {"name": "bad", "mode": "remote_inference"},
            "robot": {"type": "so101_follower"},
            "model": {"type": "mock"},
            "network": {"protocol": "udp"},
        }

        with self.assertRaisesRegex(ConfigError, "Unsupported network.protocol"):
            platform_config_from_mapping(data)

    def test_invalid_safety_range_is_rejected(self) -> None:
        data = {
            "experiment": {"name": "bad", "mode": "remote_teleoperation"},
            "robot": {"type": "so101_follower"},
            "model": {"type": "mock"},
            "teleop": {"enabled": True},
            "safety": {"action_min": 10, "action_max": 10},
        }

        with self.assertRaisesRegex(ConfigError, "safety.action_min"):
            platform_config_from_mapping(data)

    def test_invalid_print_action_interval_is_rejected(self) -> None:
        data = {
            "experiment": {"name": "bad", "mode": "debug_mock"},
            "robot": {"type": "mock"},
            "model": {"type": "mock"},
            "logging": {"print_action_interval": 0},
        }

        with self.assertRaisesRegex(ConfigError, "print_action_interval"):
            platform_config_from_mapping(data)

    def test_dataset_replay_section_is_loaded(self) -> None:
        data = {
            "experiment": {"name": "dataset-replay", "mode": "remote_teleoperation"},
            "robot": {"type": "so101_follower", "port": "/dev/ttyACM1"},
            "teleop": {"enabled": True, "type": "so101_leader", "port": "/dev/ttyACM0"},
            "model": {"type": "mock"},
            "dataset": {
                "path": "/tmp/lerobot/example",
                "episode": 1,
                "start_frame": 2,
                "end_frame": 8,
                "timing": "fixed_hz",
                "replay_frequency": 50,
            },
        }

        config = platform_config_from_mapping(data)

        self.assertEqual(config.dataset.path, "/tmp/lerobot/example")
        self.assertEqual(config.dataset.episode, 1)
        self.assertEqual(config.dataset.start_frame, 2)
        self.assertEqual(config.dataset.end_frame, 8)
        self.assertEqual(config.dataset.timing, "fixed_hz")
        self.assertEqual(config.dataset.replay_frequency, 50.0)
        self.assertEqual(config.summary()["dataset"]["path"], "/tmp/lerobot/example")

    def test_dataset_section_requires_path_when_present(self) -> None:
        data = {
            "experiment": {"name": "dataset-replay", "mode": "remote_teleoperation"},
            "robot": {"type": "so101_follower", "port": "/dev/ttyACM1"},
            "teleop": {"enabled": True, "type": "so101_leader", "port": "/dev/ttyACM0"},
            "model": {"type": "mock"},
            "dataset": {"episode": 0},
        }

        with self.assertRaisesRegex(ConfigError, "dataset.path"):
            platform_config_from_mapping(data)

    def test_dataset_timing_is_validated(self) -> None:
        data = {
            "experiment": {"name": "dataset-replay", "mode": "remote_teleoperation"},
            "robot": {"type": "so101_follower", "port": "/dev/ttyACM1"},
            "teleop": {"enabled": True, "type": "so101_leader", "port": "/dev/ttyACM0"},
            "model": {"type": "mock"},
            "dataset": {"path": "/tmp/lerobot/example", "timing": "fastish"},
        }

        with self.assertRaisesRegex(ConfigError, "Unsupported dataset.timing"):
            platform_config_from_mapping(data)

    def test_dataset_frame_range_is_validated(self) -> None:
        data = {
            "experiment": {"name": "dataset-replay", "mode": "remote_teleoperation"},
            "robot": {"type": "so101_follower", "port": "/dev/ttyACM1"},
            "teleop": {"enabled": True, "type": "so101_leader", "port": "/dev/ttyACM0"},
            "model": {"type": "mock"},
            "dataset": {"path": "/tmp/lerobot/example", "start_frame": 10, "end_frame": 2},
        }

        with self.assertRaisesRegex(ConfigError, "dataset.end_frame"):
            platform_config_from_mapping(data)

    def test_simple_yaml_parser_handles_nested_mapping_and_scalars(self) -> None:
        parsed = parse_simple_yaml(
            """
experiment:
  name: demo
  mode: remote_inference
network:
  protocol: tcp
  server_port: 9000
  reconnect: true
camera:
  cameras:
    front:
      index: 0
      width: 640
"""
        )

        self.assertEqual(parsed["experiment"]["mode"], "remote_inference")
        self.assertEqual(parsed["network"]["server_port"], 9000)
        self.assertTrue(parsed["network"]["reconnect"])
        self.assertEqual(parsed["camera"]["cameras"]["front"]["width"], 640)

    def test_script_dry_runs_print_resolved_summary(self) -> None:
        commands = [
            [
                sys.executable,
                "scripts/run_local.py",
                "--config",
                "configs/local_inference/so101_smolvla.yaml",
                "--dry-run",
            ],
            [
                sys.executable,
                "scripts/run_server.py",
                "--config",
                "configs/remote_inference/so101_smolvla.yaml",
                "--dry-run",
            ],
            [
                sys.executable,
                "scripts/run_client.py",
                "--config",
                "configs/remote_inference/so101_smolvla.yaml",
                "--dry-run",
            ],
            [
                sys.executable,
                "scripts/run_dataset_replay_client.py",
                "--config",
                "configs/replay/local_so101_tcp_dataset.yaml",
                "--dry-run",
            ],
        ]

        for command in commands:
            with self.subTest(command=command[1]):
                result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('"config"', result.stdout)
                self.assertIn('"mode"', result.stdout)

    def test_missing_config_file_returns_config_error(self) -> None:
        with TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "missing.yaml"

            with self.assertRaisesRegex(ConfigError, "Config file not found"):
                load_config(missing)


if __name__ == "__main__":
    unittest.main()
