# Validation Status

This project uses layered validation. Automated tests can prove that the Python package, thin entrypoints, dry-run path, run artifacts, reliability helpers, adapter seams, and retained legacy UDP compatibility still work. They do not prove real SO-101 hardware behavior, camera frames, SmolVLA model loading, physical control-loop stability, or 10-30 minute LAN endurance.

## Validation Matrix

| Layer | What it proves | Current status | What it does not prove |
|-------|----------------|----------------|------------------------|
| `unit-only` | Package imports, fake-LeRobot entrypoint behavior, metrics helpers, recorder helpers, reliability events, adapter placeholders, TCP teleoperation logic, and legacy protocol/runtime logic. | Passing: `python3 -m unittest discover -s tests -v` ran 106 tests. | Real LeRobot import behavior, real model loading, real cameras, serial hardware, or LAN endurance. |
| `dry-run-only` | A hardware-free path can create run directories, metadata, metrics, events, CSV, summaries, and deterministic retry/recovery events. | Passing through `tests/test_dryrun.py`. | SO-101 movement, physical safety, camera frames, real inference quality, or real network behavior. |
| `real LeRobot required` | The installed LeRobot version can import the async inference APIs and construct real server/client runtime objects. | Pending operator validation in the target Python environments. | Hardware control quality or long-running LAN stability by itself. |
| `hardware-required` | SO-101 serial access, follower calibration id, camera access, observation shape, and physical control-loop behavior. | Pending human validation on the robot-side computer. | General network endurance or future robot arms. |
| `10-30 min LAN required` | The GPU/server process and robot-side process can remain free of expected application-level crashes under the intended local network conditions. | Pending human validation through the procedure in `docs/setup/ENVIRONMENT.md`. | Public internet, VPN, non-LAN deployment, or future wireless teleoperation integration. |

## v1 Completion Boundary

Phase 5 can mark v1 code, documentation, and automated verification complete when the automated suite and documentation checks pass. That completion still leaves the real 10-30 minute LAN/hardware UAT pending until an operator runs the server and robot client on the target machines.

The current automated evidence covers RELY-04 and RELY-05:

- RELY-04: existing unit tests continue to pass after the package restructure.
- RELY-05: legacy teleoperation tests continue to pass so retained compatibility is protected.

RELY-03 remains pending human validation because unit tests use fake LeRobot modules and cannot exercise real SO-101 hardware, camera frames, SmolVLA loading, physical control, or LAN endurance.

## Legacy Compatibility

The legacy UDP teleoperation code in `legacy/` is retained compatibility/reference code. It is not the v1 main runtime path.

The current runtime package is `lerobot_remote/`. Config-driven remote inference and TCP teleoperation use `scripts/run_server.py`, `scripts/run_client.py`, and YAML files under `configs/`. The constant-based `policy_server.py` and `robot_client.py` entrypoints remain available for minimal LeRobot async compatibility. Legacy UDP tests stay in the suite so the old reference behavior is not accidentally broken while it remains in the repository.

Run the compatibility suite with:

```bash
python3 -m unittest discover -s tests -v
```

## v2 Continuation Path

The folded todo `Plan multi-arm wireless teleoperation and VLA inference` is represented here as future-work documentation only. It does not authorize Phase 5 implementation.

Separate v2 directions:

- `multi-arm support`: add real adapters and validation for additional robot arms while keeping SO-101 stable.
- `wireless teleoperation integration`: decide how legacy or future wireless teleoperation modes integrate with the current run-artifact and metrics system.
- `VLA/PI policy expansion`: add real PI-series or other VLA policy backends after the SmolVLA path is stable.
- `YAML/CLI configuration`: add saved configuration files and CLI overrides without making them a v1 blocker.
- `non-LAN deployment`: document or support VPN/cross-network experiments separately from the v1 same-LAN target.
- `reporting/plots`: add charts, time-series views, and multi-run comparisons after raw metrics are trustworthy.
