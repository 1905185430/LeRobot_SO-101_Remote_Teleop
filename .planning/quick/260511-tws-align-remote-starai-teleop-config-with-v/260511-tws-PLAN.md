# Quick Plan: Align Remote StarAI Teleop Config With Validated Local Setup

Date: 2026-05-11
Status: Complete

## Goal

Prepare `configs/teleop/remote_starai_tcp.yaml` for StarAI remote TCP teleoperation using the same hardware IDs, calibration paths, and safety settings as the validated local StarAI setup.

## Scope

- Use the project-local StarAI follower and leader calibration directories.
- Use the official LeRobot IDs already validated by local teleoperation.
- Enable `skip_initial_position` for the follower.
- Add first-frame, per-frame, and value-range safety settings.
- Enable leader action printing for remote debugging.
- Keep the existing remote endpoint `192.168.1.151:9002`.

## Verification

- `python3 scripts/run_server.py --config configs/teleop/remote_starai_tcp.yaml --dry-run`
- `python3 scripts/run_client.py --config configs/teleop/remote_starai_tcp.yaml --dry-run`
- `python3 -m unittest tests.test_config_loader tests.test_starai tests.test_tcp_teleop -v`
- `git diff --check`
