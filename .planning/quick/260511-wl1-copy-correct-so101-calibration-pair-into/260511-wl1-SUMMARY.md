# Quick Summary: Copy Correct SO101 Calibration Pair Into Repository

Date: 2026-05-11
Status: Complete

## Changes

- Added the corrected SO-101 calibration pair:
  - `calibrations/robots/so_follower/follower_arm.json`
  - `calibrations/teleoperators/so_leader/leader_arm.json`
- Updated `configs/teleop/remote_so101_tcp.yaml`:
  - follower id: `follower_arm`
  - follower calibration dir: `calibrations/robots/so_follower`
  - leader id: `leader_arm`
  - leader calibration dir: `calibrations/teleoperators/so_leader`
- Updated tests to verify SO-101 builders pass project-local calibration directories.

## Verification

- Passed: follower calibration `cmp` against cache.
- Passed: leader calibration `cmp` against cache.
- Passed: `python3 scripts/run_server.py --config configs/teleop/remote_so101_tcp.yaml --dry-run`
- Passed: `python3 scripts/run_client.py --config configs/teleop/remote_so101_tcp.yaml --dry-run`
- Passed: `python3 -m unittest tests.test_tcp_teleop tests.test_config_loader -v`
- Passed: `git diff --check`
