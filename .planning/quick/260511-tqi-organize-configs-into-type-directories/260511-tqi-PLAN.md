# Quick Plan: Organize Configs Into Type Directories

Date: 2026-05-11
Status: Complete

## Goal

Move YAML configs from a flat `configs/` directory into subdirectories grouped by runtime type.

## Scope

- Move mock configs to `configs/debug/`.
- Move local inference configs to `configs/local_inference/`.
- Move remote inference configs to `configs/remote_inference/`.
- Move teleoperation configs to `configs/teleop/`.
- Update docs, README, tests, and reproduction commands to use the new paths.
- Preserve local SO-101 teleop config edits outside this structural commit.

## Verification

- `python3 scripts/run_server.py --config configs/teleop/local_starai_tcp.yaml --dry-run`
- `python3 scripts/run_client.py --config configs/teleop/local_starai_tcp.yaml --dry-run`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`
