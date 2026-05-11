---
last_mapped: 2026-05-11
last_mapped_commit: 2dd7d89
focus: quality
---

# Testing

## Test Runner

- The README recommends `python3 -m unittest discover -s tests -v`.
- The project uses standard-library `unittest`.
- There is no CI workflow file in the repository.
- There is no coverage configuration.

## Top-Level Tests

- `tests/test_minimal_async_scripts.py` covers the current main entrypoints.
- It stubs LeRobot modules by patching `sys.modules`.
- It verifies `policy_server.build_server_config()` creates the expected config.
- It verifies `policy_server.main()` calls LeRobot `serve`.
- It verifies `robot_client.build_client_config()` passes expected robot, policy, and action settings.
- It verifies `robot_client.main()` starts the client, runs the receiver thread target, and calls `control_loop(TASK)`.

## Legacy Test Bridge

- `tests/test_legacy_demo.py` imports `ProtocolTests`, `FollowerReceiverTests`, and `LeaderSenderTests` from `legacy.tests`.
- This keeps the legacy suite reachable from the top-level `tests/` discovery command.

## Legacy Protocol Tests

- `legacy/tests/test_protocol.py` covers action round-trip encoding and decoding.
- It verifies array-like action values with `.tolist()` are supported.
- It verifies joint-name-preserving dictionary normalization.
- It rejects invalid JSON, wrong message types, missing fields, and wrong action lengths.
- It verifies action and acknowledgement message type constants.
- It covers acknowledgement round-trip encoding and decoding.

## Legacy Runtime Tests

- `legacy/tests/test_runtime.py` defines dummy leader and robot objects.
- It tests leader UDP packet sending.
- It tests monotonic leader sequence numbers.
- It tests follower receive, ACK, and action execution.
- It tests holding the last valid action during packet loss.
- It tests timeout state entry and stream recovery.
- It tests invalid packet counting.
- It tests latency stats and logging.
- It tests negative wall-clock deltas as clock skew.
- It tests leader RTT tracking from acknowledgements.

## Mocking Strategy

- Main async tests avoid real LeRobot imports through fake module objects.
- Main async tests avoid real threads by replacing `threading.Thread` with `FakeThread`.
- Legacy runtime tests use UDP localhost sockets but avoid real robot hardware.
- Legacy tests inject timestamps for deterministic timeout and latency behavior.

## Coverage Gaps

- There is no end-to-end test with a real LeRobot installation.
- There is no hardware-in-the-loop test for SO-101.
- There is no test that validates real camera configuration keys against an actual policy.
- There is no network integration test between `policy_server.py` and `robot_client.py`.
- `robot_client.py` error paths for failed start and `KeyboardInterrupt` cleanup are only partially covered.
- `policy_server.py` failure behavior from `serve(config)` is not covered.

## Practical Verification

- Use `python3 -m unittest discover -s tests -v` for repository-level verification.
- For real experiments, verify LeRobot installation separately on both server and robot machines.
- For robot-side operation, verify serial port, robot calibration id, camera name, camera index, and model path before running.
