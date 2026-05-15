---
status: complete
quick_id: 260515-nwe
date: 2026-05-15
---

# Quick Task 260515-nwe Summary

## Goal

Trim duplicate documentation and remove stale teleoperation commands after the clean-mainline refactor.

## Changes

- Rewrote `README.md` as a short landing page with only core commands and doc links.
- Rewrote `docs/README.md` as a compact document index.
- Deleted `docs/project/PROJECT_CN.md` because it duplicated README, architecture, setup, and reproduction content.
- Converted `docs/reproduction/REPRODUCTION.md` into a concise reproduction index and validation command list.
- Updated `docs/reproduction/SO101_WIRELESS_TCP_TELEOP.md` to use:
  - `scripts/run_teleop_follower.py`
  - `scripts/run_teleop_leader.py`
- Removed the stale removed-path tail from `docs/ARCHITECTURE_CN.md`.

## Verification

- `rg "docs/project|PROJECT_CN|scripts/run_server.py --config configs/teleop|scripts/run_client.py --config configs/teleop|policy_server.py|robot_client.py|legacy/|remote_teleop|docs/compatibility" -n README.md docs AGENTS.md` found no stale documentation command references.
- `python3 -m unittest discover -s tests -v` passed: 73 tests.
- `git diff --check` passed.

## Notes

- Detailed hardware runbooks remain in the two scenario-specific reproduction docs.
- `docs/setup/ENVIRONMENT.md` remains intentionally long because it covers environment and hardware preflight rather than project architecture.
