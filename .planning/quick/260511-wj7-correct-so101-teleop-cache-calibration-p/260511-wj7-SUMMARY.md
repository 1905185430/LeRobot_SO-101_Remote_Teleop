# Quick Summary: Correct SO101 Teleop Cache Calibration Pair

Date: 2026-05-11
Status: Complete

## Changes

- Corrected SO-101 remote teleop IDs:
  - follower: `follower_arm`
  - leader: `leader_arm`
- Kept `calibration_dir: null` for both devices so LeRobot loads:
  - `~/.cache/huggingface/lerobot/calibration/robots/so_follower/follower_arm.json`
  - `~/.cache/huggingface/lerobot/calibration/teleoperators/so_leader/leader_arm.json`
- Updated TCP teleop tests to expect the corrected cache IDs.

## Verification

- Passed: `python3 scripts/run_server.py --config configs/teleop/remote_so101_tcp.yaml --dry-run`
- Passed: `python3 scripts/run_client.py --config configs/teleop/remote_so101_tcp.yaml --dry-run`
- Passed: `python3 -m unittest tests.test_tcp_teleop tests.test_config_loader -v`
- Passed: `git diff --check`
