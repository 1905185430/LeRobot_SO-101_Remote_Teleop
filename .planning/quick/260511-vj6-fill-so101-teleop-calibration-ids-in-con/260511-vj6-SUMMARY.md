# Quick Summary: Fill SO101 Teleop Calibration IDs In Config

Date: 2026-05-11
Status: Complete

## Changes

- Added project-local SO-101 calibration files:
  - `calibrations/robots/so_follower/my_awesome_follower_arm.json`
  - `calibrations/teleoperators/so_leader/so101_leader_arm.json`
- Updated `configs/teleop/remote_so101_tcp.yaml`:
  - follower id: `my_awesome_follower_arm`
  - follower calibration dir: `calibrations/robots/so_follower`
  - leader id: `so101_leader_arm`
  - leader calibration dir: `calibrations/teleoperators/so_leader`
- Updated SO-101 TCP teleop builders to pass `calibration_dir` into LeRobot config objects.
- Added test coverage for SO-101 project-local calibration directory propagation.

## Verification

- Passed: `python3 scripts/run_server.py --config configs/teleop/remote_so101_tcp.yaml --dry-run`
- Passed: `python3 scripts/run_client.py --config configs/teleop/remote_so101_tcp.yaml --dry-run`
- Passed: `python3 -m unittest tests.test_tcp_teleop tests.test_config_loader -v`
- Passed: `python3 -m unittest discover -s tests -v`
- Passed: `git diff --check`
