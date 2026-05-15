---
status: complete
quick_id: 260515-nqp
date: 2026-05-15
---

# Quick Task 260515-nqp Summary

## Goal

Create a clean latest-mainline codebase by removing legacy UDP teleoperation, root constant-based entrypoints, and compatibility shims while preserving config-driven remote inference and TCP teleoperation.

## Changes

- Removed root constant-based entrypoints:
  - `policy_server.py`
  - `robot_client.py`
- Removed legacy UDP teleoperation:
  - `legacy/`
  - `tests/test_legacy_demo.py`
- Removed constant-entrypoint runtime modules and tests:
  - `lerobot_remote/server.py`
  - `lerobot_remote/client.py`
  - `tests/test_minimal_async_scripts.py`
- Removed teleoperation compatibility shim:
  - `lerobot_remote/runtime/remote_teleop.py`
- Moved SO-101 action normalization into `lerobot_remote/teleop/actions.py` so mainline TCP teleop no longer depends on `legacy.protocol`.
- Updated README, architecture, setup, validation, project, and agent guidance to describe the config-driven mainline only.
- Added `.gitignore` entries for local runtime artifacts and editor/assistant state.
- Restored `configs/teleop/local_starai_tcp.yaml` to the tracked safe default.

## Verification

- `python3 scripts/run_teleop_follower.py --config configs/teleop/local_starai_tcp.yaml --dry-run` passed.
- `python3 scripts/run_teleop_leader.py --config configs/teleop/local_starai_tcp.yaml --dry-run` passed.
- `python3 scripts/run_server.py --config configs/remote_inference/so101_smolvla.yaml --dry-run` passed.
- `python3 scripts/run_client.py --config configs/remote_inference/so101_smolvla.yaml --dry-run` passed.
- `python3 -m unittest discover -s tests -v` passed.

## Notes

- Ignored local directories/files remain on disk but no longer pollute `git status`: `.codex/`, `.vscode/`, `logs/`, `runs/`, and `map.png`.
- Real hardware runtime was not executed.
