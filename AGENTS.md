<!-- GSD:project-start source:PROJECT.md -->
## Project

**SO-101 Remote VLA Inference Experiments**

This project is a lightweight remote VLA inference experiment framework for SO-101 first, with SmolVLA as the first real policy path. It keeps the current LeRobot async inference direction, but reorganizes the code into a small package with thin CLIs, communication metrics, dry-run support, and enough adapter boundaries to later add PI-series policies and other robot arms.

The goal is not to build a highly integrated robotics platform. The goal is to make remote inference run reliably on a GPU server plus robot-side computer over a local network, record communication parameters clearly, and keep the code structure clean enough for the next experiments.

**Core Value:** SO-101 + SmolVLA remote inference must run stably while producing trustworthy communication metrics that can be used for wireless communication experiments.

### Constraints

- **Runtime**: Python + LeRobot — the project should build around the existing LeRobot async inference path.
- **Topology**: GPU server plus robot-side computer on the same LAN for v1 — this is the first deployment target.
- **Robot**: SO-101 is the first supported hardware — other arms are roadmap items.
- **Policy**: SmolVLA is the first supported VLA policy — PI-series policies are roadmap items.
- **Configuration**: v1 may keep script constants — do not block early progress on a large YAML/CLI config system.
- **Architecture**: small package + thin CLIs — enough structure for testing and reuse, not a platform rewrite.
- **Metrics**: communication measurements must be structured and saved — terminal-only logs are not enough.
- **Safety**: hardware-facing failures must be visible in logs — timeout/disconnect/exception events should not fail silently.
- **Documentation**: environment setup guidance must be available before serious hardware experiments — setup uncertainty invalidates metrics.
- **Compatibility**: legacy teleoperation behavior should remain tested while it is retained.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

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
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Code Style
- Python code uses `from __future__ import annotations`.
- Functions and variables use snake case.
- Constants use upper snake case.
- Classes use PascalCase.
- Public functions generally have short docstrings.
- The current main scripts are intentionally thin wrappers around LeRobot APIs.
## Configuration Style
- Main-path configuration is constant-based and edited directly in `policy_server.py` and `robot_client.py`.
- The README explicitly tells users to edit constants before running scripts.
- Legacy CLIs use `argparse` flags instead of hard-coded operator settings.
- Empty `configs/` directories exist, but there is no active config loading layer.
## Dependency Handling
- Optional or environment-specific LeRobot imports are delayed until runtime.
- Main scripts raise user-facing `RuntimeError` messages when LeRobot is unavailable.
- `robot_client.py` tries multiple SO-101 follower config module paths to preserve compatibility across LeRobot versions.
- Tests use fake modules in `sys.modules` instead of requiring LeRobot to be installed.
## Error Handling
- `ProtocolError` is used for invalid legacy UDP payloads.
- Legacy loops catch `KeyboardInterrupt` and return `0`.
- Legacy CLI `main()` functions log exceptions and return `1`.
- Legacy cleanup uses broad `Exception` catches only for best-effort disconnect cleanup.
- Main `robot_client.py` stops and joins on `KeyboardInterrupt`, but normal cleanup for non-interrupt failure paths is minimal.
## Runtime Loop Patterns
- Legacy loops use a fixed `period_s = 1.0 / hz`.
- Legacy loops advance `next_tick` and sleep for remaining time.
- If the loop falls behind, `next_tick` is reset to `time.perf_counter()`.
- Legacy sockets are set to non-blocking mode.
## Protocol Patterns
- Legacy JSON payloads use compact separators and ASCII encoding.
- Legacy messages include explicit `msg_type` fields.
- Legacy action values are normalized to floats.
- Legacy action dictionaries must include all expected SO-101 joint keys.
- Legacy sequence numbers must be non-negative integers and monotonic on the follower.
## Logging
- `legacy/logging_utils.py` defines a shared log format.
- Legacy leader logs RTT summaries.
- Legacy follower logs latency summaries, timeout state, stream recovery, invalid packets, and clock skew warnings.
- Main LeRobot scripts rely mostly on upstream LeRobot behavior and minimal local messages.
## Comments And Language
- Current main scripts contain bilingual English and Chinese comments/docstrings.
- Legacy protocol contains extensive Chinese explanatory comments.
- Tests use English names and assertions.
## Testing Conventions
- Tests are standard-library `unittest`, not `pytest`.
- Hardware and LeRobot are mocked or stubbed.
- Socket behavior is tested with localhost UDP socket pairs.
- Timing-sensitive behavior is tested by injecting timestamps where possible.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Overview
- The current main path is a minimal wrapper around official LeRobot async inference.
- The legacy path is a custom UDP teleoperation bridge retained as reference code.
## Main Async Inference Flow
## Main Entry Points
- `policy_server.py:main()` is the server entrypoint.
- `policy_server.py:build_server_config()` is the server config factory.
- `robot_client.py:main()` is the robot client entrypoint.
- `robot_client.py:build_camera_configs()` creates OpenCV camera configs.
- `robot_client.py:build_robot_config()` creates the SO-101 follower config.
- `robot_client.py:build_client_config()` creates the LeRobot async client config.
## Dependency Loading
- `policy_server.py` uses `_load_server_api()` to delay LeRobot imports until runtime.
- `robot_client.py` uses `_load_client_api()` to delay LeRobot imports until runtime.
- `robot_client.py` uses `_load_so101_follower_config()` to try multiple LeRobot module paths.
- Tests rely on this lazy-loading boundary to stub LeRobot modules in `sys.modules`.
## Legacy UDP Flow
## Legacy Core Abstractions
- `legacy.protocol.ActionMessage` models leader-to-follower action packets.
- `legacy.protocol.AckMessage` models follower-to-leader acknowledgements.
- `legacy.protocol.ProtocolError` identifies invalid wire payloads.
- `legacy.leader_sender.LeaderSender` owns sequence numbers, UDP sends, ACK polling, RTT metrics, and loop pacing.
- `legacy.follower_receiver.FollowerReceiver` owns datagram validation, ACK sending, timeout behavior, latency metrics, and loop pacing.
## Data Contracts
- Main path uses LeRobot config object contracts.
- Legacy action packets use `msg_type = "action_v1"`.
- Legacy acknowledgement packets use `msg_type = "action_ack_v1"`.
- Legacy action shape is six named SO-101 joint positions:
## Error Handling
- Main scripts convert missing LeRobot imports into `RuntimeError` messages that tell the operator to install LeRobot.
- `robot_client.py:main()` handles `KeyboardInterrupt` by stopping the client and joining the receiver thread.
- Legacy CLIs catch startup/runtime exceptions, log stack traces, and return exit code `1`.
- Legacy cleanup paths attempt best-effort hardware disconnect and socket close.
## Architectural Direction
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
