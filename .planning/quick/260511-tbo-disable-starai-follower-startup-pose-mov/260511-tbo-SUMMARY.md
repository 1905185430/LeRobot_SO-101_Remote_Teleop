# Quick Summary: Disable StarAI Follower Startup Pose Move

Date: 2026-05-11
Status: Complete

## Changes

- Added `robot.skip_initial_position` to `RobotConfig`.
- Added StarAI follower startup protection that skips `move_to_initial_position()` when configured.
- Enabled `skip_initial_position: true` in `configs/local_teleop_starai_tcp.yaml`.
- Added tests proving the default StarAI path still moves when not configured, and the local teleop config skips the startup move.

## Operator Notes

The local StarAI server should now print:

```text
StarAI follower startup initial-position move skipped by config.
```

This only disables the follower's automatic startup pose move. It does not bypass later TCP action validation, first-action delta checks, or per-frame action delta limits.

## Verification

- Passed: `python3 -m unittest tests.test_starai -v`
- Passed: `python3 -m unittest tests.test_config_loader -v`
- Passed: `python3 -m unittest tests.test_tcp_teleop -v`
- Passed: `python3 scripts/run_server.py --config configs/local_teleop_starai_tcp.yaml --dry-run`
- Passed: `python3 -m unittest discover -s tests -v`
- Passed: `git diff --check`
