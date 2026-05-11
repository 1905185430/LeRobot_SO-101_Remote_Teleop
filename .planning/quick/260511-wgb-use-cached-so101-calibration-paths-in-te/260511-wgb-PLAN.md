# Quick Plan: Use Cached SO101 Calibration Paths In Teleop Config

Date: 2026-05-11
Status: Complete

## Goal

Configure SO-101 remote teleoperation to use the matching LeRobot cache calibration files by ID instead of a project-local calibration directory.

## Scope

- Identify available SO-101 follower and leader calibration files in the local LeRobot cache.
- Keep the matching IDs in `configs/teleop/remote_so101_tcp.yaml`.
- Set `calibration_dir: null` so LeRobot resolves calibration from each machine's own cache directory.
- Update TCP teleop tests to reflect cache-based calibration lookup.

## Verification

- `python3 scripts/run_server.py --config configs/teleop/remote_so101_tcp.yaml --dry-run`
- `python3 scripts/run_client.py --config configs/teleop/remote_so101_tcp.yaml --dry-run`
- `python3 -m unittest tests.test_tcp_teleop tests.test_config_loader -v`
- `git diff --check`
