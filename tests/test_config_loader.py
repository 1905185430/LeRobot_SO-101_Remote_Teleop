from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from so101_remote.config_loader import load_config, parse_simple_yaml
from so101_remote.config_schema import ConfigError, platform_config_from_mapping


ROOT = Path(__file__).resolve().parents[1]


class ConfigLoaderTests(unittest.TestCase):
    def test_load_remote_inference_config(self) -> None:
        config = load_config(ROOT / "configs" / "remote_inference_so101_smolvla.yaml")

        self.assertEqual(config.mode, "remote_inference")
        self.assertEqual(config.robot.type, "so101_follower")
        self.assertEqual(config.model.type, "smolvla")
        self.assertEqual(config.network.protocol, "tcp")
        self.assertEqual(config.network.endpoint, "192.168.1.151:9000")
        self.assertEqual(sorted(config.camera.cameras), ["front", "wrist"])
        self.assertTrue(config.webui.enabled)

    def test_load_local_inference_config(self) -> None:
        config = load_config(ROOT / "configs" / "local_inference_so101_smolvla.yaml")

        self.assertEqual(config.mode, "local_inference")
        self.assertEqual(config.network.server_host, "127.0.0.1")
        self.assertFalse(config.webui.enabled)
        self.assertEqual(config.safety.max_action_delta, 2.0)

    def test_load_local_starai_teleop_safety_config(self) -> None:
        config = load_config(ROOT / "configs" / "local_teleop_starai_tcp.yaml")

        self.assertEqual(config.safety.max_action_delta, 1.0)
        self.assertEqual(config.safety.max_first_action_delta, 12.0)
        self.assertEqual(config.safety.action_min, -100)
        self.assertEqual(config.safety.action_max, 100)
        self.assertTrue(config.safety.require_action_keys_match)
        self.assertTrue(config.robot.skip_initial_position)
        self.assertTrue(config.logging.print_leader_actions)
        self.assertEqual(config.logging.print_action_interval, 10)

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
                "configs/local_inference_so101_smolvla.yaml",
                "--dry-run",
            ],
            [
                sys.executable,
                "scripts/run_server.py",
                "--config",
                "configs/remote_inference_so101_smolvla.yaml",
                "--dry-run",
            ],
            [
                sys.executable,
                "scripts/run_client.py",
                "--config",
                "configs/remote_inference_so101_smolvla.yaml",
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
