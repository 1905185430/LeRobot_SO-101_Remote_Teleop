---
quick_id: 260511-qas
slug: implement-config-driven-tcp-teleoperatio
type: quick
status: complete
completed_at: 2026-05-11
---

# Quick Task Summary: Implement config-driven TCP teleoperation runtime

## Completed

- Added `so101_remote.teleop_tcp` with TCP SO-101 leader and follower runtime classes.
- Added `TcpTeleopLeaderClient` to read leader `get_action()`, normalize SO-101 joint actions, send length-prefixed `ACTION` messages, and validate `ACK` responses.
- Added `TcpTeleopFollowerServer` to accept one TCP client, validate monotonic `ACTION` frames, call follower `send_action()`, return `ACK`, and hold the last action on socket timeout when configured.
- Added lazy LeRobot builders for SO-101 leader and follower devices.
- Wired `remote_teleoperation` into `scripts/run_server.py` and `scripts/run_client.py` through `so101_remote.runtime`.
- Added fake-device unit tests for settings, action normalization, duplicate frame rejection, runtime dispatch, and localhost TCP ACTION/ACK roundtrip.
- Updated Chinese and English docs with TCP teleoperation commands and boundaries.

## Verification

- `python3 -m unittest tests.test_tcp_teleop -v`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/run_server.py --config configs/remote_teleop_so101_tcp.yaml --dry-run`
- `python3 scripts/run_client.py --config configs/remote_teleop_so101_tcp.yaml --dry-run`
- `git diff --check`
