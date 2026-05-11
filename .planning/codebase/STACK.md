---
last_mapped: 2026-05-11
last_mapped_commit: 2dd7d89
focus: tech
---

# Stack

## Runtime

- **Language**: Python 3.
- **Entry style**: direct executable scripts guarded by `if __name__ == "__main__"`.
- **Package manager metadata**: none found. There is no `pyproject.toml`, `setup.py`, `requirements.txt`, or lockfile in the repository.
- **Primary dependency**: LeRobot, imported lazily so tests and static inspection can run without the package installed.

## Main Application Path

- `policy_server.py` starts a LeRobot async inference policy server on `HOST` and `PORT`.
- `robot_client.py` starts a LeRobot robot-side async inference client for SO-101.
- `README.md` states the intended workflow: run `policy_server.py` on the server or GPU machine and `robot_client.py` on the robot-side computer.
- Main-path configuration is currently hard-coded as constants at the top of the scripts rather than loaded from config files.

## LeRobot APIs Used

- `policy_server.py` imports `PolicyServerConfig` from `lerobot.async_inference.configs`.
- `policy_server.py` imports `serve` from `lerobot.async_inference.policy_server`.
- `robot_client.py` imports `RobotClientConfig` from `lerobot.async_inference.configs`.
- `robot_client.py` imports `RobotClient` from `lerobot.async_inference.robot_client`.
- `robot_client.py` imports `visualize_action_queue_size` from `lerobot.async_inference.helpers`.
- `robot_client.py` imports `OpenCVCameraConfig` from `lerobot.cameras.opencv.configuration_opencv`.
- `robot_client.py` tries multiple module paths for `SO101FollowerConfig` to tolerate LeRobot version drift.

## Legacy Path

- `legacy/leader_sender.py` implements a leader-side UDP action sender using `socket`, `argparse`, `logging`, and LeRobot SO-101 leader APIs.
- `legacy/follower_receiver.py` implements a follower-side UDP receiver using `socket`, `argparse`, `logging`, and LeRobot SO-101 follower APIs.
- `legacy/protocol.py` defines the custom JSON-over-UDP message contract with dataclasses.
- `legacy/logging_utils.py` contains shared logging setup for the legacy scripts.

## Standard Library Dependencies

- `argparse` for CLI parsing in `legacy/leader_sender.py` and `legacy/follower_receiver.py`.
- `dataclasses`, `json`, and `typing` for the protocol helpers in `legacy/protocol.py`.
- `importlib.import_module` in `robot_client.py` to lazily load optional LeRobot modules.
- `logging` for runtime visibility.
- `socket` for UDP transport in the legacy path.
- `threading` for the robot client action receiver thread.
- `time` for control-loop pacing, latency, RTT, and timeout calculations.
- `unittest`, `types`, and `unittest.mock` for tests.

## Configuration

- `policy_server.py` exposes `HOST = "0.0.0.0"` and `PORT = 8080`.
- `robot_client.py` exposes constants for server address, serial port, robot id, cameras, task text, policy type, model path, device, action chunking, aggregation, and debug visualization.
- Empty directories exist for `configs/policy_server` and `configs/robot_client`, but the current README explicitly says there is no local config layer in the main path.

## Tooling

- Tests run with `python3 -m unittest discover -s tests -v`.
- No formatter, linter, CI config, or dependency installer is defined in the repository.
- Generated caches are present in `__pycache__/`, `legacy/__pycache__/`, `legacy/tests/__pycache__/`, and `so101_async/__pycache__/`.
