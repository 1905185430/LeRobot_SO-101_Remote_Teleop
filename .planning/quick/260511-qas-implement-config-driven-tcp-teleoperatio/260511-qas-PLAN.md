---
quick_id: 260511-qas
slug: implement-config-driven-tcp-teleoperatio
type: quick
status: planned
requirements: []
must_haves:
  truths:
    - "remote_teleoperation server starts a TCP follower receiver from config."
    - "remote_teleoperation client starts a TCP leader sender from config."
    - "Leader sends normalized ACTION messages and follower returns ACK messages over length-prefixed TCP."
    - "Follower applies actions through LeRobot SO-101 follower send_action and supports timeout hold behavior."
    - "Tests cover TCP teleop with fake devices and no LeRobot install."
  artifacts:
    - path: "so101_remote/teleop_tcp.py"
      provides: "Config-driven TCP teleoperation sender and receiver"
---

# Quick Task: Implement config-driven TCP teleoperation runtime

## Scope

Implement the first real config-driven TCP remote teleoperation path for SO-101 leader/follower. Keep it simple and testable: one TCP client, continuous ACTION/ACK stream, fake-device unit tests, and lazy LeRobot imports.

## Tasks

1. Add TCP teleop module.
   - Files: `so101_remote/teleop_tcp.py`
   - Verify: fake leader/follower roundtrip sends actions and ACKs.

2. Wire config runtime.
   - Files: `so101_remote/runtime.py`
   - Verify: `remote_teleoperation` no longer raises placeholder errors.

3. Update docs.
   - Files: `docs/PROJECT_CN.md`, `README.md`
   - Verify: commands describe TCP teleop server/client.

4. Run regression tests.
   - Verify: `python3 -m unittest discover -s tests -v` and `git diff --check`.
