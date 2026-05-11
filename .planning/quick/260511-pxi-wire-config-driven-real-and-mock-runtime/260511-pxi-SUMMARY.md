---
quick_id: 260511-pxi
slug: wire-config-driven-real-and-mock-runtime
type: quick
status: complete
completed_at: 2026-05-11
---

# Quick Task Summary: Wire config-driven real and mock runtime

## Completed

- Added `so101_remote.runtime` to dispatch config-driven server/client/local entrypoints.
- Wired `scripts/run_server.py` and `scripts/run_client.py` so `remote_inference` starts the real LeRobot async server/client path when LeRobot is installed.
- Wired `debug_mock` so server/client can run one hardware-free TCP observation/action roundtrip.
- Kept unsupported real modes explicit: local LeRobot inference, config-driven TCP teleoperation, and WebUI are documented next steps rather than silent placeholders.
- Added runtime tests with fake LeRobot modules and a real localhost TCP mock roundtrip.
- Added `docs/PROJECT_CN.md` with Chinese architecture, usage, debugging, artifacts, and current limitations.
- Updated `README.md` to point at the Chinese guide and describe the current executable paths.

## Verification

- `python3 -m unittest tests.test_configured_runtime -v`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`
- `python3 scripts/run_local.py --config configs/debug_mock_robot.yaml`
