# Quick Task 260515-nqp: Clean Mainline Codebase - Plan

**Mode:** quick
**Created:** 2026-05-15
**Status:** Ready

## Goal

Make the repository a clean latest-mainline project by removing legacy UDP teleoperation, constant-based compatibility entrypoints, and teleop compatibility shims while preserving config-driven remote inference and TCP teleoperation.

## Task 1: Remove legacy dependencies from main package

**Files**
- `lerobot_remote/teleop/actions.py`
- `lerobot_remote/teleop/server.py`
- `lerobot_remote/runtime/__init__.py`
- `lerobot_remote/runtime/dispatch.py`

**Action**
- Inline SO-101 action keys and action normalization into `teleop/actions.py`.
- Remove all imports from `legacy`.
- Remove references to `runtime.remote_teleop`.

**Verify**
- `rg "from legacy|import legacy|remote_teleop" lerobot_remote tests`

## Task 2: Delete old code and old tests

**Files**
- `legacy/`
- `policy_server.py`
- `robot_client.py`
- `tests/test_legacy_demo.py`
- `tests/test_minimal_async_scripts.py`
- `lerobot_remote/runtime/remote_teleop.py`
- `docs/compatibility/LEGACY_ENTRYPOINTS_CN.md`

**Action**
- Delete compatibility and legacy surfaces.
- Keep config-driven runtime, policy builders, and tests.

**Verify**
- `python3 -m unittest discover -s tests -v`

## Task 3: Clean docs and working tree noise

**Files**
- `.gitignore`
- `README.md`
- `docs/ARCHITECTURE_CN.md`
- `docs/setup/ENVIRONMENT.md`
- `docs/validation/VALIDATION.md`
- `docs/project/PROJECT_CN.md`
- `.planning/STATE.md`

**Action**
- Remove legacy/compatibility language from docs.
- Add ignores for local artifacts (`logs/`, `runs/`, `.vscode/`, `.codex/`, `map.png`, extra caches).
- Restore uncommitted local config drift in `configs/teleop/local_starai_tcp.yaml`.

**Verify**
- `git status --short` contains only intended staged changes before commit.
- Dry-run main scripts:
  - `python3 scripts/run_teleop_follower.py --config configs/teleop/local_starai_tcp.yaml --dry-run`
  - `python3 scripts/run_teleop_leader.py --config configs/teleop/local_starai_tcp.yaml --dry-run`
  - `python3 scripts/run_server.py --config configs/remote_inference/so101_smolvla.yaml --dry-run`
  - `python3 scripts/run_client.py --config configs/remote_inference/so101_smolvla.yaml --dry-run`
