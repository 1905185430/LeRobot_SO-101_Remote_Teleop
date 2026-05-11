# Quick Plan: Disable StarAI Follower Startup Pose Move

Date: 2026-05-11
Status: Complete

## Goal

Prevent the StarAI follower from automatically moving to the official package's hard-coded initial pose when starting TCP teleoperation server.

## Scope

- Add `robot.skip_initial_position` to platform config.
- When enabled for StarAI follower, replace the instance `move_to_initial_position()` with a no-op before `connect()`.
- Enable the setting in the local StarAI TCP teleoperation config.
- Add tests for config parsing and StarAI startup behavior.

## Verification

- `python3 -m unittest tests.test_starai -v`
- `python3 -m unittest tests.test_config_loader -v`
- `python3 -m unittest tests.test_tcp_teleop -v`
- `python3 scripts/run_server.py --config configs/local_teleop_starai_tcp.yaml --dry-run`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`
