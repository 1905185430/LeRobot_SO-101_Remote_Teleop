# Quick Task 260519-ltc: Document Local SO-101 TCP Teleoperation - Plan

**Mode:** quick
**Created:** 2026-05-19
**Status:** Ready

## Goal

Add a reproduction document for local SO-101 TCP teleoperation under `docs/reproduction`.

## Task 1: Add Reproduction Doc

**Files**
- `docs/reproduction/SO101_LOCAL_TCP_TELEOP.md`

**Action**
- Document the local SO-101 TCP config, serial ports, calibration pair, safety settings, startup commands, stop order, run artifacts, dry-run commands, tests, and common failures.
- Keep the structure aligned with existing StarAI local and SO-101 wireless reproduction docs.

**Verify**
- Confirm commands and config values match `configs/teleop/local_so101_tcp.yaml`.
- Run dry-run commands for follower and leader if dependencies are available.

## Task 2: Link From Index

**Files**
- `docs/reproduction/REPRODUCTION.md`

**Action**
- Add the local SO-101 TCP reproduction guide to the reproduction index and quick dry-run section.

**Verify**
- `git diff --check`

## Task 3: Keep Documented Tests Runnable

**Files**
- `lerobot_remote/teleop/actions.py`

**Action**
- Remove Python 3.10-only `zip(..., strict=True)` from SO-101 action normalization because the length check already enforces strictness.

**Verify**
- `python3 -m unittest tests.test_config_loader tests.test_tcp_teleop -v`
