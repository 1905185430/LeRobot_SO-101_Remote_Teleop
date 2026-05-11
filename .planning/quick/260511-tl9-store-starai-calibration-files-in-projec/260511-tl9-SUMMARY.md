# Quick Summary: Store StarAI Calibration Files In Project Directory

Date: 2026-05-11
Status: Complete

## Changes

- Added project-local StarAI calibration files:
  - `calibrations/robots/starai_viola/my_awesome_staraiviola_arm.json`
  - `calibrations/teleoperators/starai_violin/my_awesome_staraiviolin_arm.json`
- Updated `configs/local_teleop_starai_tcp.yaml` to use those calibration directories and the official LeRobot IDs.
- Added `teleop.calibration_dir` to config parsing.
- Updated StarAI builders to pass `calibration_dir` into official LeRobot robot and teleoperator configs.
- Added tests for local calibration paths and StarAI config construction.

## Verification

- Passed: `python3 -m unittest tests.test_config_loader tests.test_starai -v`
- Passed: `python3 scripts/run_server.py --config configs/local_teleop_starai_tcp.yaml --dry-run`
- Passed: `python3 -m unittest discover -s tests -v`
- Passed: `git diff --check`
