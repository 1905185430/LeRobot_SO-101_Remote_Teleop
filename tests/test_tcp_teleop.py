from __future__ import annotations

from dataclasses import replace
import socket
import threading
import time
import unittest
from tempfile import TemporaryDirectory
from unittest import mock

from so101_remote.config_loader import load_config
from so101_remote.runtime import run_configured_client, run_configured_server
from so101_remote.teleop_tcp import (
    TcpTeleopFollowerServer,
    TcpTeleopLeaderClient,
    tcp_teleop_settings,
    validate_action_values,
)


JOINTS = {
    "shoulder_pan.pos": 0.1,
    "shoulder_lift.pos": -0.2,
    "elbow_flex.pos": 0.3,
    "wrist_flex.pos": 0.4,
    "wrist_roll.pos": -0.5,
    "gripper.pos": 0.6,
}


class FakeLeader:
    def __init__(self) -> None:
        self.actions_read = 0

    def get_action(self):
        self.actions_read += 1
        return {key: value + self.actions_read for key, value in JOINTS.items()}


class FailingLeader:
    def get_action(self):
        raise TypeError("'>=' not supported between instances of 'NoneType' and 'int'")


class FakeFollower:
    def __init__(self) -> None:
        self.actions: list[dict[str, float]] = []

    def send_action(self, action) -> None:
        self.actions.append(dict(action))

    def get_observation(self) -> dict[str, float]:
        return {key: 0.0 for key in JOINTS}


def free_local_endpoint() -> tuple[str, int]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    host, port = sock.getsockname()
    sock.close()
    return host, port


def with_endpoint(config, save_dir: str, host: str, port: int):
    return replace(
        config,
        experiment=replace(config.experiment, save_dir=save_dir),
        network=replace(config.network, server_host=host, server_port=port, timeout_ms=1000),
        runtime=replace(config.runtime, action_send_frequency=1000.0, control_frequency=1000.0),
    )


def with_safety(config, **kwargs):
    return replace(config, safety=replace(config.safety, **kwargs))


class TcpTeleopTests(unittest.TestCase):
    def test_settings_are_loaded_from_remote_teleop_config(self) -> None:
        config = load_config("configs/remote_teleop_so101_tcp.yaml")

        settings = tcp_teleop_settings(config)

        self.assertEqual(settings.host, config.network.server_host)
        self.assertEqual(settings.port, config.network.server_port)
        self.assertEqual(settings.leader_id, config.teleop.id)
        self.assertEqual(settings.follower_id, config.robot.id)

    def test_leader_builds_normalized_action_messages(self) -> None:
        config = load_config("configs/remote_teleop_so101_tcp.yaml")
        client = TcpTeleopLeaderClient(FakeLeader(), tcp_teleop_settings(config))

        message = client.build_action_message()

        self.assertEqual(message["type"], "ACTION")
        self.assertEqual(message["frame_id"], 0)
        self.assertEqual(sorted(message["action"]), sorted(JOINTS))

    def test_leader_read_failure_is_wrapped_before_send(self) -> None:
        config = load_config("configs/remote_teleop_so101_tcp.yaml")
        client = TcpTeleopLeaderClient(FailingLeader(), tcp_teleop_settings(config))

        with self.assertRaisesRegex(RuntimeError, "Failed to read a safe leader action"):
            client.build_action_message()

    def test_follower_rejects_duplicate_frames(self) -> None:
        config = load_config("configs/remote_teleop_so101_tcp.yaml")
        server = TcpTeleopFollowerServer(FakeFollower(), tcp_teleop_settings(config))
        server.last_action = dict(JOINTS)
        message = {
            "type": "ACTION",
            "frame_id": 1,
            "timestamp_ns": time.time_ns(),
            "action": JOINTS,
        }

        server.handle_action_message(message)

        with self.assertRaisesRegex(ValueError, "Out-of-order"):
            server.handle_action_message(message)

    def test_follower_limits_large_action_delta_from_current_position(self) -> None:
        config = with_safety(
            load_config("configs/remote_teleop_so101_tcp.yaml"),
            max_first_action_delta=200.0,
        )
        server = TcpTeleopFollowerServer(FakeFollower(), tcp_teleop_settings(config))
        server.initialize_action_baseline()

        limited = server.handle_action_message(
            {
                "type": "ACTION",
                "frame_id": 1,
                "timestamp_ns": time.time_ns(),
                "action": {key: 100.0 for key in JOINTS},
            }
        )

        self.assertTrue(all(value == 2.0 for value in limited.values()))

    def test_follower_rejects_first_action_too_far_from_startup_pose(self) -> None:
        config = with_safety(
            load_config("configs/remote_teleop_so101_tcp.yaml"),
            max_first_action_delta=1.0,
        )
        server = TcpTeleopFollowerServer(FakeFollower(), tcp_teleop_settings(config))
        server.initialize_action_baseline()

        with self.assertRaisesRegex(ValueError, "First ACTION is too far"):
            server.handle_action_message(
                {
                    "type": "ACTION",
                    "frame_id": 1,
                    "timestamp_ns": time.time_ns(),
                    "action": {key: 10.0 for key in JOINTS},
                }
            )

    def test_follower_rejects_mismatched_action_keys(self) -> None:
        config = load_config("configs/remote_teleop_so101_tcp.yaml")
        server = TcpTeleopFollowerServer(FakeFollower(), tcp_teleop_settings(config))
        server.initialize_action_baseline()

        with self.assertRaisesRegex(ValueError, "ACTION keys do not match"):
            server.handle_action_message(
                {
                    "type": "ACTION",
                    "frame_id": 1,
                    "timestamp_ns": time.time_ns(),
                    "action": {"wrong_joint.pos": 0.0},
                }
            )

    def test_validate_action_values_rejects_nan_and_range(self) -> None:
        with self.assertRaisesRegex(ValueError, "not finite"):
            validate_action_values({"joint.pos": float("nan")}, action_min=-100, action_max=100)
        with self.assertRaisesRegex(ValueError, "outside"):
            validate_action_values({"joint.pos": 101.0}, action_min=-100, action_max=100)

    def test_tcp_teleop_roundtrip_with_fake_devices(self) -> None:
        host, port = free_local_endpoint()
        with TemporaryDirectory() as tmpdir:
            config = with_endpoint(load_config("configs/remote_teleop_so101_tcp.yaml"), tmpdir, host, port)
            settings = tcp_teleop_settings(config)
            leader = FakeLeader()
            follower = FakeFollower()
            server = TcpTeleopFollowerServer(follower, settings)
            client = TcpTeleopLeaderClient(leader, settings)
            errors: list[BaseException] = []

            def serve() -> None:
                try:
                    server.run(max_messages=3)
                except BaseException as exc:  # pragma: no cover - surfaced below
                    errors.append(exc)

            thread = threading.Thread(target=serve, daemon=True)
            thread.start()
            time.sleep(0.02)

            result = client.run(max_messages=3)
            thread.join(timeout=2.0)

        self.assertEqual(result, 0)
        self.assertFalse(errors)
        self.assertFalse(thread.is_alive())
        self.assertEqual(leader.actions_read, 3)
        self.assertEqual(len(follower.actions), 3)

    def test_runtime_dispatches_remote_teleoperation(self) -> None:
        config = load_config("configs/remote_teleop_so101_tcp.yaml")

        with mock.patch("so101_remote.runtime.run_tcp_teleop_follower_server", return_value=0) as server:
            self.assertEqual(run_configured_server(config), 0)
        with mock.patch("so101_remote.runtime.run_tcp_teleop_leader_client", return_value=0) as client:
            self.assertEqual(run_configured_client(config), 0)

        server.assert_called_once_with(config)
        client.assert_called_once_with(config)


if __name__ == "__main__":
    unittest.main()
