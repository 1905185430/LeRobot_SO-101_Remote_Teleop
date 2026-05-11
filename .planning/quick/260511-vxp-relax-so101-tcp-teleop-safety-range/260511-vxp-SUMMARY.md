# Quick Summary: Relax SO101 TCP Teleop Safety Range

Date: 2026-05-11
Status: Complete

## Changes

- Added explicit SO-101 TCP teleop safety settings:
  - `max_action_delta: 2.0`
  - `max_first_action_delta: 25.0`
  - `action_min: -180`
  - `action_max: 180`
  - `require_action_keys_match: true`
- This addresses follower startup observations such as `shoulder_lift.pos=-121.582` being rejected before the TCP server can listen.

## Verification

- Passed: `python3 scripts/run_server.py --config configs/teleop/remote_so101_tcp.yaml --dry-run`
- Passed: `python3 scripts/run_client.py --config configs/teleop/remote_so101_tcp.yaml --dry-run`
- Passed: `python3 -m unittest tests.test_tcp_teleop tests.test_config_loader -v`
- Passed: `git diff --check`
