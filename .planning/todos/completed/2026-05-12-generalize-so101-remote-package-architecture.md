---
created: 2026-05-12T01:59:21.426Z
title: Generalize so101_remote package architecture
area: planning
files:
  - so101_remote/
  - so101_remote/starai.py
  - so101_remote/teleop_tcp.py
  - so101_remote/runtime.py
  - scripts/run_server.py
  - scripts/run_client.py
  - scripts/run_local.py
  - docs/project/PROJECT_CN.md
---

## Problem

The project package is still named `so101_remote`, but the repository has already moved beyond a single SO-101-only implementation. It now includes validated SO-101 wireless TCP teleoperation, validated StarAI local TCP teleoperation, StarAI-specific integration code, multi-config YAML organization, and a renamed repository identity: `lerobot-remote-vla-teleop`.

Keeping StarAI and future robot support under a package named `so101_remote` creates architectural confusion:

- `so101_remote/starai.py` places StarAI support inside a package named after another robot model.
- Future robot arms would make the mismatch worse.
- `teleop_tcp.py` and `runtime.py` are growing into broad platform modules rather than SO-101-specific modules.
- The package name no longer matches the project direction: LeRobot-based remote VLA inference and TCP teleoperation across multiple robot backends.

The current working SO-101 and StarAI teleoperation paths must not be broken by this cleanup.

## Solution

Plan this as a staged architecture change rather than a large behavior rewrite.

Recommended first stage:

- Rename the Python package from `so101_remote` to `lerobot_remote`.
- Update imports in scripts, tests, docs, and package modules.
- Keep the existing CLI commands unchanged:
  - `python3 scripts/run_server.py --config ...`
  - `python3 scripts/run_client.py --config ...`
  - `python3 scripts/run_local.py --config ...`
- Preserve a temporary compatibility shim under `so101_remote/` if needed so older imports fail gracefully or continue to work during migration.
- Verify that SO-101 wireless TCP teleoperation and StarAI local TCP teleoperation configs still load and pass automated tests.

Recommended second stage:

- Split robot-specific code into `lerobot_remote/robots/`:
  - `robots/so101.py`
  - `robots/starai.py`
  - `robots/factory.py`
- Split TCP teleoperation code into `lerobot_remote/teleop/`:
  - `teleop/client.py`
  - `teleop/server.py`
  - `teleop/settings.py`
  - `teleop/actions.py`
  - `teleop/safety.py`
- Split runtime dispatch into `lerobot_remote/runtime/`:
  - `runtime/dispatch.py`
  - `runtime/remote_teleop.py`
  - `runtime/remote_inference.py`
  - `runtime/debug_mock.py`
  - `runtime/local_inference.py`
- Later consider moving metrics/recorder to `recording/` and policy code to `policies/`.

Suggested planning decision:

Use a new phase for this, with Phase 6 focused only on `so101_remote -> lerobot_remote` package migration and compatibility. Defer deeper internal module splitting to a later phase after the renamed package is stable.
