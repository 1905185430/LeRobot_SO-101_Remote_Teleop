---
status: complete
quick_id: 260519-ltc
date: 2026-05-19
---

# Quick Task 260519-ltc Summary

## Goal

Write a local TCP SO-101 teleoperation reproduction guide under `docs/reproduction`.

## Changes

- Added `docs/reproduction/SO101_LOCAL_TCP_TELEOP.md`.
- Linked the new guide from `docs/reproduction/REPRODUCTION.md`.
- Documented the local SO-101 TCP config, serial ports, calibration pair, safety settings, startup commands, stop order, WebUI, run artifacts, dry-run commands, tests, and common failures.
- Replaced Python 3.10-only `zip(..., strict=True)` in SO-101 action normalization with normal `zip(...)`; the existing length check already enforces strictness and this keeps the documented `python3` tests runnable on Python 3.9.

## Verification

- `python3 scripts/run_teleop_follower.py --config configs/teleop/local_so101_tcp.yaml --dry-run` passed.
- `python3 scripts/run_teleop_leader.py --config configs/teleop/local_so101_tcp.yaml --dry-run` passed.
- `python3 -m unittest tests.test_config_loader tests.test_tcp_teleop -v` passed: 23 tests.
- `git diff --check` passed.
