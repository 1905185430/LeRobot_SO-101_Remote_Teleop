---
last_mapped: 2026-05-11
last_mapped_commit: 2dd7d89
focus: arch
---

# Architecture

## Overview

This repository currently has two layers of implementation:

- The current main path is a minimal wrapper around official LeRobot async inference.
- The legacy path is a custom UDP teleoperation bridge retained as reference code.

The README positions the main path as the recommended workflow for SmolVLA wireless inference experiments, with `legacy/` kept for the older custom UDP teleop approach.

## Main Async Inference Flow

1. `policy_server.py` runs on the server or GPU machine.
2. `policy_server.py` builds `PolicyServerConfig(host=HOST, port=PORT)`.
3. `policy_server.py` calls LeRobot `serve(config)` and then blocks.
4. `robot_client.py` runs on the robot-side computer.
5. `robot_client.py` builds camera config, SO-101 follower config, and `RobotClientConfig`.
6. `robot_client.py` starts `RobotClient`.
7. `robot_client.py` starts a daemon thread for `client.receive_actions`.
8. `robot_client.py` runs `client.control_loop(TASK)` in the main thread.

This architecture intentionally leaves inference transport, observation sending, action queueing, and robot execution to LeRobot.

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

1. `legacy/leader_sender.py` reads local leader arm actions.
2. `legacy/protocol.py` normalizes actions into six SO-101 joint keys.
3. `legacy/leader_sender.py` sends compact JSON action datagrams over UDP.
4. `legacy/follower_receiver.py` receives datagrams, validates sequencing and schema, and stores the latest valid action.
5. `legacy/follower_receiver.py` sends UDP acknowledgements back to the leader.
6. `legacy/follower_receiver.py` drives the follower robot with the latest valid action, holding the last known position on timeout.

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
  - `shoulder_pan.pos`
  - `shoulder_lift.pos`
  - `elbow_flex.pos`
  - `wrist_flex.pos`
  - `wrist_roll.pos`
  - `gripper.pos`

## Error Handling

- Main scripts convert missing LeRobot imports into `RuntimeError` messages that tell the operator to install LeRobot.
- `robot_client.py:main()` handles `KeyboardInterrupt` by stopping the client and joining the receiver thread.
- Legacy CLIs catch startup/runtime exceptions, log stack traces, and return exit code `1`.
- Legacy cleanup paths attempt best-effort hardware disconnect and socket close.

## Architectural Direction

The current codebase is moving away from bespoke UDP teleoperation and toward official LeRobot async inference. The new main path is deliberately small and mostly config assembly; most behavior lives in upstream LeRobot.
