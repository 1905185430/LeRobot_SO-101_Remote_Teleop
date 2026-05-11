---
phase: 04-so-101-smolvla-runtime-integration
status: draft
created: 2026-05-11
source: 04-RESEARCH.md
---

# Phase 04 Validation Strategy

## Validation Architecture

Phase 04 verification must prove both package-level runtime integration and operator-facing reproducibility without requiring LeRobot or SO-101 hardware in unit tests.

## Automated Checks

- `python3 -m unittest tests.test_minimal_async_scripts -v`
- `python3 -m unittest tests.test_recorder tests.test_reliability tests.test_minimal_async_scripts -v`
- `python3 -m unittest discover -s tests -v`
- `rg "run_policy_server|run_robot_client|server_settings|client_settings" so101_remote`
- `rg "policy-server|robot-client|resolved_settings" tests so101_remote`

## Manual / Hardware Checks

- On the GPU/server machine, run `python3 policy_server.py` in a LeRobot environment and confirm a policy-server run directory is created.
- On the robot-side machine, run `python3 robot_client.py` in a LeRobot + SO-101 environment and confirm a robot-client run directory is created.
- For RELY-03, perform a 10-30 minute LAN run and record whether application-level crashes occur. This is a hardware validation item; unit tests can only verify readiness and instrumentation.

## Known Limits

- Unit tests must use fake LeRobot modules and cannot prove model loading, camera frames, serial control, or physical behavior.
- Latency and queue metrics should not be claimed unless LeRobot exposes the required signal.
