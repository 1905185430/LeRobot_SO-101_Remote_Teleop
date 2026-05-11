# Phase 5 Pattern Map

**Phase:** 05-validation-and-compatibility-hardening
**Generated:** 2026-05-11

## Planning Context

Phase 5 is a validation and documentation closure phase. It should preserve existing runtime behavior, protect retained legacy compatibility, and document validation boundaries and v2 continuation paths. It should not add new runtime capabilities.

## Existing Patterns To Reuse

### Test Runner
- Use standard-library `unittest`.
- Repository-level verification command is `python3 -m unittest discover -s tests -v`.
- Focused test modules are invoked with `python3 -m unittest tests.test_minimal_async_scripts -v` and related module names.

### Fake-LeRobot Testing
- `tests/test_minimal_async_scripts.py` stubs LeRobot modules in `sys.modules`.
- Runtime tests avoid requiring LeRobot or hardware.
- Tests assert official LeRobot config object construction and wrapper behavior through fake classes.

### Legacy Compatibility Testing
- `tests/test_legacy_demo.py` imports test classes from `legacy.tests` so top-level discovery runs retained UDP teleoperation coverage.
- `legacy/tests/test_protocol.py` covers wire encoding/decoding and payload validation.
- `legacy/tests/test_runtime.py` covers UDP send/receive, ACKs, packet loss hold behavior, timeouts, latency logging, clock skew, and RTT tracking.

### Validation Documentation
- `docs/ENVIRONMENT.md` already distinguishes real LAN readiness from unit-test proof.
- `.planning/phases/04-so-101-smolvla-runtime-integration/04-VERIFICATION.md` records automated PASS plus human-needed RELY-03.
- `.planning/phases/04-so-101-smolvla-runtime-integration/04-HUMAN-UAT.md` persists pending real LAN/hardware validation.

## Closest Analogs

| Phase 5 target | Closest existing analog | Reuse guidance |
|---|---|---|
| Full automated verification command set | `tests/test_legacy_demo.py`, `tests/test_minimal_async_scripts.py`, `tests/test_recorder.py`, `tests/test_reliability.py`, `tests/test_dryrun.py` | Keep commands standard-library only; avoid adding pytest/CI tooling. |
| Legacy compatibility status | `README.md` `## Legacy` section | Extend status wording without changing legacy runtime behavior. |
| Validation boundary docs | `docs/ENVIRONMENT.md` `## 10-30 Minute LAN Experiment Readiness` | Add or reference a strict validation matrix that separates automated vs hardware-required checks. |
| v2 continuation path | `.planning/REQUIREMENTS.md` `## v2 Requirements` and `.planning/PROJECT.md` deferred/out-of-scope sections | Split future directions into separate items rather than one broad bucket. |

## Planning Constraints

- Do not introduce multi-arm runtime support, wireless teleoperation integration, new VLA policy backends, YAML/CLI configuration, reporting dashboards, or non-LAN deployment.
- Small fixes are allowed only for tests, docs, compatibility glue, or clear correctness issues found during verification.
- Do not close hardware/LAN UAT unless the real 10-30 minute run has actually been performed.
