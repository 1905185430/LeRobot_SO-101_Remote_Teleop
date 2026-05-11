# Quick Plan: Relax SO101 TCP Teleop Safety Range

Date: 2026-05-11
Status: Complete

## Goal

Allow valid SO-101 follower startup readings that can exceed the default `[-100, 100]` normalized range while keeping teleoperation safety checks enabled.

## Scope

- Add an explicit `safety` block to `configs/teleop/remote_so101_tcp.yaml`.
- Set SO-101 TCP teleop action range to `[-180, 180]`.
- Keep first-action delta, per-frame delta, and key-match checks enabled.

## Verification

- `python3 scripts/run_server.py --config configs/teleop/remote_so101_tcp.yaml --dry-run`
- `python3 scripts/run_client.py --config configs/teleop/remote_so101_tcp.yaml --dry-run`
- `python3 -m unittest tests.test_tcp_teleop tests.test_config_loader -v`
- `git diff --check`
