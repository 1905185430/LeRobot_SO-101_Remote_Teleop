# Quick Summary: Organize Configs Into Type Directories

Date: 2026-05-11
Status: Complete

## Changes

- Reorganized configs into:
  - `configs/debug/`
  - `configs/local_inference/`
  - `configs/remote_inference/`
  - `configs/teleop/`
- Updated `configs/README.md` with the new directory layout.
- Updated `README.md`, `docs/PROJECT_CN.md`, and `docs/REPRODUCTION.md` commands.
- Updated tests to load configs from the new paths.

## Verification

- Passed: `python3 scripts/run_server.py --config configs/teleop/local_starai_tcp.yaml --dry-run`
- Passed: `python3 scripts/run_client.py --config configs/teleop/local_starai_tcp.yaml --dry-run`
- Passed: `python3 -m unittest discover -s tests -v`
- Passed: `git diff --check`
