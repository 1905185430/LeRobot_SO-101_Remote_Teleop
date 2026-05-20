from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from lerobot_remote.config.schema import DatasetReplayConfig
from lerobot_remote.replay import (
    DatasetReplayError,
    DatasetReplayTcpClient,
    InMemoryDatasetActionSource,
    LeRobotDatasetActionSource,
    require_dataset_path,
)
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


if __name__ == "__main__":
    unittest.main()
