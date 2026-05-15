---
status: complete
quick_id: 260515-mrg
date: 2026-05-15
---

# Quick Task 260515-mrg Summary

## Goal

Improve architecture understandability for the config-driven TCP teleoperation and remote inference project without breaking validated StarAI/SO101 teleoperation paths.

## Changes

- Added role-explicit TCP teleoperation entrypoints:
  - `scripts/run_teleop_follower.py`
  - `scripts/run_teleop_leader.py`
- Moved real teleoperation orchestration into `lerobot_remote/runtime/teleoperation.py`.
- Kept `lerobot_remote/runtime/remote_teleop.py` as a compatibility shim for old imports.
- Updated runtime dispatch and package exports to use the clearer teleoperation module.
- Added `docs/ARCHITECTURE_CN.md` with operator and maintainer views of the active architecture.
- Added `docs/compatibility/LEGACY_ENTRYPOINTS_CN.md` to mark old paths as transitional and define removal prerequisites.
- Updated README and StarAI reproduction docs to prefer role-explicit teleoperation commands.

## Verification

- `python3 scripts/run_teleop_follower.py --config configs/teleop/local_starai_tcp.yaml --dry-run` passed.
- `python3 scripts/run_teleop_leader.py --config configs/teleop/local_starai_tcp.yaml --dry-run` passed.
- `python3 scripts/run_server.py --config configs/teleop/local_starai_tcp.yaml --dry-run` passed.
- `python3 scripts/run_client.py --config configs/teleop/local_starai_tcp.yaml --dry-run` passed.
- `python3 -m unittest tests.test_tcp_teleop tests.test_configured_runtime tests.test_starai -v` passed: 24 tests.

## Notes

- Existing user-local changes in `configs/teleop/local_starai_tcp.yaml`, `runs/`, `logs/`, `.codex/`, `.vscode/`, and `map.png` were not modified or staged by this task.
- No hardware-connected runtime was executed during verification.
