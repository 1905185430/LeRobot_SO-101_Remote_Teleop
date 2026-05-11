# Quick Summary: Document Config Categories And Validation Reproduction Commands

Date: 2026-05-11
Status: Complete

## Changes

- Added `configs/README.md` with configuration categories:
  - Debug / Mock
  - Local Inference
  - Remote Inference
  - TCP Teleoperation
- Added `docs/REPRODUCTION.md` with:
  - StarAI local TCP teleoperation server/client commands
  - dry-run commands
  - targeted test commands
  - full test command
  - safety notes for first-frame delta rejection

## Verification

- Passed: `python3 -m unittest tests.test_config_loader tests.test_starai tests.test_tcp_teleop -v`
- Passed: local StarAI config path exists.
- Passed: both project-local StarAI calibration files exist.
