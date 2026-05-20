from __future__ import annotations

from dataclasses import replace
import json
import socket
import sys
import threading
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import time
from unittest import mock

from lerobot_remote.config.loader import load_config
from lerobot_remote.config.schema import DatasetReplayConfig
from lerobot_remote.replay import (
    DatasetReplayError,
    DatasetReplayTcpClient,
    InMemoryDatasetActionSource,
    LeRobotDatasetActionSource,
    require_dataset_path,
)
from lerobot_remote.runtime import run_dataset_replay_client
from lerobot_remote.teleop import TcpTeleopFollowerServer, tcp_teleop_settings
from lerobot_remote.teleop.settings import TcpTeleopSettings


JOINTS = {
    "shoulder_pan.pos": 0.1,
    "shoulder_lift.pos": -0.2,
    "elbow_flex.pos": 0.3,
    "wrist_flex.pos": 0.4,
    "wrist_roll.pos": -0.5,
    "gripper.pos": 0.6,
}


class FakeLeRobotDataset:
    fps = 50
    num_frames = 3

    def __init__(self, repo_id, root, episodes, local_files_only=True):
        self.repo_id = repo_id
        self.root = root
        self.episodes = episodes
        self.local_files_only = local_files_only
        self.samples = [
            {"action": [0, 1, 2, 3, 4, 5], "timestamp": 0.0},
            {"action": [1, 2, 3, 4, 5, 6], "timestamp": 0.02},
            {"action": [2, 3, 4, 5, 6, 7], "timestamp": 0.04},
        ]

    def __getitem__(self, index):
        return self.samples[index]


class FakeFollower:
    def __init__(self) -> None:
        self.actions: list[dict[str, float]] = []

    def send_action(self, action) -> None:
        self.actions.append(dict(action))

    def get_observation(self) -> dict[str, float]:
        return {key: 0.0 for key in JOINTS}


class DatasetReplayTests(unittest.TestCase):
    def test_in_memory_source_produces_ordered_normalized_frames(self) -> None:
        source = InMemoryDatasetActionSource([list(JOINTS.values()), JOINTS], replay_frequency=50)

        frames = list(source)

        self.assertEqual([frame.frame_id for frame in frames], [0, 1])
        self.assertEqual([frame.dataset_index for frame in frames], [0, 1])
        self.assertEqual(sorted(frames[0].action), sorted(JOINTS))
        self.assertEqual(source.info.frame_count, 2)
        self.assertEqual(source.info.timing, "fixed_hz")

    def test_in_memory_source_supports_frame_slice(self) -> None:
        source = InMemoryDatasetActionSource(
            [[0, 1, 2, 3, 4, 5], [1, 2, 3, 4, 5, 6], [2, 3, 4, 5, 6, 7]],
            start_frame=1,
            end_frame=2,
        )

        frames = list(source)

        self.assertEqual([frame.dataset_index for frame in frames], [1, 2])
        self.assertEqual(frames[0].action["shoulder_pan.pos"], 1.0)

    def test_source_timestamps_require_timestamps(self) -> None:
        with self.assertRaisesRegex(DatasetReplayError, "source_timestamps"):
            InMemoryDatasetActionSource([JOINTS], timing="source_timestamps")

    def test_require_dataset_path_fails_before_network_side_effects(self) -> None:
        with TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "missing"

            with self.assertRaisesRegex(DatasetReplayError, "does not exist"):
                require_dataset_path(DatasetReplayConfig(path=str(missing)))

    def test_lerobot_import_failure_is_actionable(self) -> None:
        with TemporaryDirectory() as tmpdir:
            with mock.patch.dict(sys.modules, {"lerobot": None}):
                with self.assertRaisesRegex(DatasetReplayError, "LeRobot"):
                    LeRobotDatasetActionSource(DatasetReplayConfig(path=tmpdir))

    def test_lerobot_source_reads_actions_with_lazy_imported_dataset(self) -> None:
        with TemporaryDirectory() as tmpdir:
            datasets_module = types.ModuleType("lerobot.datasets")
            datasets_module.LeRobotDataset = FakeLeRobotDataset
            lerobot_module = types.ModuleType("lerobot")
            with mock.patch.dict(
                sys.modules,
                {
                    "lerobot": lerobot_module,
                    "lerobot.datasets": datasets_module,
                },
            ):
                source = LeRobotDatasetActionSource(
                    DatasetReplayConfig(
                        path=tmpdir,
                        episode=0,
                        start_frame=1,
                        end_frame=2,
                        timing="source_timestamps",
                    )
                )

        frames = list(source)

        self.assertEqual(source.info.frame_count, 2)
        self.assertEqual(source.info.source_fps, 50.0)
        self.assertEqual([frame.dataset_index for frame in frames], [1, 2])
        self.assertEqual([frame.timestamp_s for frame in frames], [0.02, 0.04])
        self.assertEqual(frames[0].action["shoulder_pan.pos"], 1.0)

    def test_tcp_client_builds_dataset_action_message(self) -> None:
        source = InMemoryDatasetActionSource([JOINTS], dataset_path="/tmp/demo")
        client = DatasetReplayTcpClient(
            source,
            source.info,
            _settings(),
        )

        message = client.build_action_message(list(source)[0])

        self.assertEqual(message["type"], "ACTION")
        self.assertEqual(message["frame_id"], 0)
        self.assertEqual(message["dataset_frame"], 0)
        self.assertEqual(message["leader_id"], "dataset_replay")
        self.assertEqual(message["action"], JOINTS)

    def test_tcp_client_rejects_out_of_range_action_before_send(self) -> None:
        source = InMemoryDatasetActionSource([{**JOINTS, "gripper.pos": 999.0}])
        client = DatasetReplayTcpClient(source, source.info, _settings())

        with self.assertRaisesRegex(Exception, "outside"):
            client.build_action_message(list(source)[0])

    def test_dataset_replay_tcp_roundtrip_with_fake_follower(self) -> None:
        host, port = _free_local_endpoint()
        with TemporaryDirectory() as tmpdir:
            config = _with_endpoint(load_config("configs/replay/local_so101_tcp_dataset.yaml"), tmpdir, host, port)
            config = replace(
                config,
                safety=replace(config.safety, max_first_action_delta=200.0, max_action_delta=200.0),
            )
            settings = tcp_teleop_settings(config)
            follower = FakeFollower()
            server = TcpTeleopFollowerServer(follower, settings)
            source = InMemoryDatasetActionSource([JOINTS, {key: value + 0.1 for key, value in JOINTS.items()}], replay_frequency=1000)
            client = DatasetReplayTcpClient(source, source.info, settings)
            errors: list[BaseException] = []

            def serve() -> None:
                try:
                    server.run(max_messages=2)
                except BaseException as exc:  # pragma: no cover - surfaced below
                    errors.append(exc)

            thread = threading.Thread(target=serve, daemon=True)
            thread.start()
            time.sleep(0.02)

            result = client.run()
            thread.join(timeout=2.0)

        self.assertEqual(result, 0)
        self.assertFalse(errors)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(follower.actions), 2)
        self.assertEqual(follower.actions[0], JOINTS)

    def test_runtime_writes_dataset_replay_artifacts_for_fake_run(self) -> None:
        host, port = _free_local_endpoint()
        with TemporaryDirectory() as tmpdir:
            config = _with_endpoint(load_config("configs/replay/local_so101_tcp_dataset.yaml"), tmpdir, host, port)
            config = replace(
                config,
                safety=replace(config.safety, max_first_action_delta=200.0, max_action_delta=200.0),
            )
            settings = tcp_teleop_settings(config)
            follower = FakeFollower()
            server = TcpTeleopFollowerServer(follower, settings)
            errors: list[BaseException] = []

            def serve() -> None:
                try:
                    server.run(max_messages=1)
                except BaseException as exc:  # pragma: no cover - surfaced below
                    errors.append(exc)

            thread = threading.Thread(target=serve, daemon=True)
            thread.start()
            time.sleep(0.02)

            result = run_dataset_replay_client(
                config,
                source_factory=lambda _config: InMemoryDatasetActionSource(
                    [JOINTS],
                    dataset_path=_config.dataset.path or "",
                    episode=_config.dataset.episode,
                    replay_frequency=1000,
                ),
            )
            thread.join(timeout=2.0)
            run_dirs = sorted(Path(tmpdir).glob("*-dataset-replay-client-*"))
            self.assertEqual(result, 0)
            self.assertFalse(errors)
            self.assertFalse(thread.is_alive())
            self.assertEqual(len(follower.actions), 1)
            self.assertEqual(len(run_dirs), 1)
            run_dir = run_dirs[0]
            for artifact in (
                "metadata.json",
                "events.jsonl",
                "metrics.jsonl",
                "metrics.csv",
                "summary.md",
                "config.yaml",
            ):
                self.assertTrue((run_dir / artifact).exists(), artifact)
            metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
            replay_metadata = metadata["extra"]["dataset_replay"]
            self.assertEqual(replay_metadata["dataset_path"], "/tmp/lerobot/so101_dataset")
            self.assertEqual(replay_metadata["episode"], 0)
            self.assertEqual(replay_metadata["frame_count"], 1)
            self.assertEqual(metadata["extra"]["tcp_endpoint"], f"{host}:{port}")
            self.assertIn(
                "dataset_replay_complete",
                (run_dir / "events.jsonl").read_text(encoding="utf-8"),
            )

    def test_runtime_validates_dataset_path_before_socket_connection(self) -> None:
        with TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "missing-dataset"
            config = replace(
                load_config("configs/replay/local_so101_tcp_dataset.yaml"),
                experiment=replace(
                    load_config("configs/replay/local_so101_tcp_dataset.yaml").experiment,
                    save_dir=tmpdir,
                ),
                dataset=DatasetReplayConfig(path=str(missing)),
            )

            with mock.patch("socket.create_connection") as create_connection:
                with self.assertRaisesRegex(DatasetReplayError, "does not exist"):
                    run_dataset_replay_client(config)

        create_connection.assert_not_called()


def _settings() -> TcpTeleopSettings:
    return TcpTeleopSettings(
        host="127.0.0.1",
        port=1,
        timeout_s=0.1,
        max_packet_size=1024 * 1024,
        send_hz=50.0,
        control_hz=50.0,
        leader_id="dataset_replay",
        follower_id="follower_arm",
        hold_last_action_on_timeout=True,
        max_action_delta=2.0,
        max_first_action_delta=55.0,
        action_min=-180.0,
        action_max=180.0,
        require_action_keys_match=True,
        print_leader_actions=False,
        print_action_interval=10,
    )


def _free_local_endpoint() -> tuple[str, int]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    host, port = sock.getsockname()
    sock.close()
    return host, port


def _with_endpoint(config, save_dir: str, host: str, port: int):
    return replace(
        config,
        experiment=replace(config.experiment, save_dir=save_dir),
        network=replace(config.network, server_host=host, server_port=port, timeout_ms=1000),
        runtime=replace(config.runtime, action_send_frequency=1000.0, control_frequency=1000.0),
    )


if __name__ == "__main__":
    unittest.main()
