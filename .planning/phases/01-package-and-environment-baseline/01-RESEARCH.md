# Phase 1 Research: Package And Environment Baseline

**Phase:** 1 — Package And Environment Baseline  
**Date:** 2026-05-11  
**Status:** Complete  

## Research Question

What needs to be known to plan Phase 1 well: establishing a lightweight `so101_remote/` package, keeping `policy_server.py` and `robot_client.py` as thin entrypoints, preserving `legacy/`, documenting constants, and writing `docs/ENVIRONMENT.md`.

## Existing Code Facts

- `policy_server.py` is currently a direct server entrypoint with constants `HOST` and `PORT`, a `build_server_config()` helper, `_load_server_api()`, and `main()`.
- `robot_client.py` is currently a direct robot-side entrypoint with constants for server address, SO-101 port/id, camera config, task text, policy type, model path, device, action chunking, aggregation, and queue visualization.
- Both current entrypoints use lazy LeRobot imports so unit tests can run without LeRobot installed.
- `legacy/` already exists as a Python package and contains the old custom UDP teleoperation path.
- `tests/test_minimal_async_scripts.py` imports the current top-level entrypoints and stubs LeRobot modules.
- `tests/test_legacy_demo.py` keeps legacy tests reachable from top-level unittest discovery.
- `docs/`, `configs/`, and `scripts/` exist but are currently empty.

## Recommended Technical Approach

### Package Structure

Create the smallest package that gives future phases stable import locations without moving too much behavior at once:

```text
so101_remote/
  __init__.py
  server.py
  client.py
  config.py
  metrics.py
  recorder.py
  dryrun.py
  adapters/
    __init__.py
    robot.py
    policy.py
    lerobot_so101.py
```

For Phase 1, these modules can be mostly scaffolding. The important behavior is that `policy_server.py` and `robot_client.py` remain runnable and delegate to package modules.

### Thin Entrypoints

- `policy_server.py` should keep operator-facing constants or import them from `so101_remote.config`, then delegate runtime construction to `so101_remote.server`.
- `robot_client.py` should keep operator-facing constants or import them from `so101_remote.config`, then delegate runtime construction to `so101_remote.client`.
- Preserve existing function names where tests or users rely on them: `build_server_config()`, `build_client_config()`, `build_robot_config()`, `build_camera_configs()`, and `main()`.
- Keep lazy LeRobot import behavior in package modules or wrappers; do not introduce import-time LeRobot requirements.

### Legacy Boundary

- Keep `legacy/` as an isolated package.
- Do not import `legacy/` from the new main runtime path in Phase 1.
- Preserve `tests/test_legacy_demo.py` and `legacy/tests/`.
- Add tests that prove top-level discovery still runs both current async script tests and legacy tests.

### Documentation

`docs/ENVIRONMENT.md` should be a first-class deliverable, not a vague README note. It should cover:

- GPU/server setup: Python, LeRobot install, CUDA/PyTorch checks, SmolVLA model path, HuggingFace access, server preflight.
- Robot-side setup: Python, LeRobot install, SO-101 serial permissions, follower calibration id, camera detection, client preflight.
- LAN checks: IP/port, firewall, ping/basic connectivity, time synchronization for metric trust.
- Dry-run/mock setup: how to validate runtime and metrics without hardware once dry-run exists.
- Common failures: LeRobot import failure, CUDA unavailable, invalid model path, camera index mismatch, serial permission failure, server connection failure, metrics output confusion.

## Phase Risks

- Moving functions too aggressively can break current tests and direct script usage.
- Importing LeRobot at module import time will break local tests that intentionally stub dependencies.
- Documentation can drift from constants if constants are duplicated in too many places.
- Existing worktree is dirty and contains untracked runtime files; execution must work with those files rather than reverting them.

## Validation Architecture

Use the existing standard-library unittest setup as the validation base.

- Quick command: `python3 -m unittest tests.test_minimal_async_scripts -v`
- Full command: `python3 -m unittest discover -s tests -v`
- Required checks:
  - `python3 -m unittest discover -s tests -v` exits 0.
  - `python3 -c "import so101_remote; import so101_remote.server; import so101_remote.client"` exits 0.
  - `policy_server.py` still exposes `build_server_config` and `main`.
  - `robot_client.py` still exposes `build_client_config`, `build_robot_config`, `build_camera_configs`, and `main`.
  - `docs/ENVIRONMENT.md` contains the setup sections named in this research.

## Planning Implications

Plan 1 should create the package skeleton and thin entrypoint handoff.  
Plan 2 should preserve legacy/test boundaries and update tests to match the new imports.  
Plan 3 should write the environment guide and constant-editing documentation.

## RESEARCH COMPLETE
