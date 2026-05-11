# Quick Summary: Use Cached SO101 Calibration Paths In Teleop Config

Date: 2026-05-11
Status: Complete

## Cache Files Found

- Follower cache candidates:
  - `/home/xuan/.cache/huggingface/lerobot/calibration/robots/so_follower/follower_arm.json`
  - `/home/xuan/.cache/huggingface/lerobot/calibration/robots/so_follower/my_awesome_follower_arm.json`
- Leader cache candidates:
  - `/home/xuan/.cache/huggingface/lerobot/calibration/teleoperators/so_leader/leader_arm.json`
  - `/home/xuan/.cache/huggingface/lerobot/calibration/teleoperators/so_leader/so101_leader_arm.json`

## Changes

- `configs/teleop/remote_so101_tcp.yaml` now uses:
  - follower id: `my_awesome_follower_arm`
  - follower `calibration_dir: null`
  - leader id: `so101_leader_arm`
  - leader `calibration_dir: null`
- With `calibration_dir: null`, LeRobot resolves calibration from the current user's cache on each machine.
- Updated tests to assert SO-101 teleop builders rely on cache calibration by default.

## Verification

- Passed: `python3 scripts/run_server.py --config configs/teleop/remote_so101_tcp.yaml --dry-run`
- Passed: `python3 scripts/run_client.py --config configs/teleop/remote_so101_tcp.yaml --dry-run`
- Passed: `python3 -m unittest tests.test_tcp_teleop tests.test_config_loader -v`
- Passed: `git diff --check`
