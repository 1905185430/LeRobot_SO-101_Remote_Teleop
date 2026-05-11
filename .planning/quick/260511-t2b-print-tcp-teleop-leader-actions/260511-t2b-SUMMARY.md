# Quick Summary: Print TCP Teleop Leader Actions

Date: 2026-05-11
Status: Complete

## Changes

- Added `logging.print_leader_actions` and `logging.print_action_interval` to the platform config schema.
- Added interval-based terminal printing in `TcpTeleopLeaderClient` after safe leader action normalization and before TCP send.
- Enabled leader action printing every 10 frames in `configs/local_teleop_starai_tcp.yaml`.
- Added tests for config validation and print behavior.

## Operator Notes

When enabled, the client terminal prints lines like:

```text
Leader action frame=0: Motor_0.pos=0.000, Motor_1.pos=1.000
```

Printing only happens after the leader device returns a valid action. If the StarAI motor API still raises the `NoneType` position error while reading the leader, no unsafe action is sent and there is no action value to print.

## Verification

- Passed: `python3 -m unittest tests.test_tcp_teleop -v`
- Passed: `python3 -m unittest tests.test_config_loader -v`
- Passed: `python3 scripts/run_client.py --config configs/local_teleop_starai_tcp.yaml --dry-run`
- Passed: `python3 -m unittest discover -s tests -v`
- Passed: `git diff --check`
