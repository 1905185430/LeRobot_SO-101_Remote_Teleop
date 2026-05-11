---
phase: 04-so-101-smolvla-runtime-integration
verified: 2026-05-11T04:32:11Z
status: human_needed
score: 12/12 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Run the real policy server and SO-101 robot client together on the target LAN for 10-30 minutes."
    expected: "Both real LeRobot processes remain free of expected application-level crashes and each side writes metadata.json, events.jsonl, and summary.md under logs/experiments/."
    why_human: "Unit tests use fake LeRobot modules and cannot validate real SO-101 hardware, camera frames, model loading, LAN behavior, or the physical control loop required by RELY-03."
---

# Phase 4: SO-101 SmolVLA Runtime Integration Verification Report

**Phase Goal:** Route the real LeRobot async inference server and client through the new package while preserving the official transport path.
**Verified:** 2026-05-11T04:32:11Z
**Status:** human_needed
**Re-verification:** No - initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Operator can start the SmolVLA policy server through the thin entrypoint. | VERIFIED | `policy_server.py:5-9` imports package helpers and calls `main()` only; `so101_remote/server.py:38-40` delegates to `run_policy_server()`. |
| 2 | Operator can start the SO-101 robot client through the thin entrypoint. | VERIFIED | `robot_client.py:5-31` re-exports package constants/helpers and calls package `main()` only; `so101_remote/client.py:103-105` delegates to `run_robot_client()`. |
| 3 | Policy server startup still uses official LeRobot async inference `serve(config)`. | VERIFIED | `so101_remote/server.py:32-35` builds `PolicyServerConfig`; `so101_remote/server.py:59-61` passes that config to official `serve(config)`. Test `test_policy_server_main_calls_serve` asserts the fake official serve is called once. |
| 4 | Robot client startup still uses official LeRobot `RobotClient` and `RobotClientConfig`. | VERIFIED | `so101_remote/client.py:85-100` builds `RobotClientConfig`; `so101_remote/client.py:121-148` constructs `RobotClient(config)`, starts it, starts `receive_actions`, and runs `control_loop(TASK)`. |
| 5 | Robot client exposes required SO-101, camera, model, action chunking, aggregation, and debug settings. | VERIFIED | `so101_remote/config.py:11-35` defines all operator constants; `so101_remote/client.py:28-43` exposes them via `client_settings()`; `tests/test_minimal_async_scripts.py:236-258` verifies the complete key set. |
| 6 | Server startup creates per-run artifacts and resolved settings metadata. | VERIFIED | `so101_remote/server.py:43-63` creates a `policy-server` run directory, writes metadata through `JsonlMetricsRecorder`, records startup event, writes summary; `tests/test_minimal_async_scripts.py:193-209` asserts `metadata.json`, `events.jsonl`, `summary.md`, role, endpoint, and recovery event. |
| 7 | Client startup creates per-run artifacts and resolved settings metadata. | VERIFIED | `so101_remote/client.py:108-150` creates a `robot-client` run directory, writes metadata, records recovery event, writes summary; `tests/test_minimal_async_scripts.py:288-308` asserts `metadata.json`, `events.jsonl`, `summary.md`, role, robot id, server address, and recovery event. |
| 8 | Server startup records diagnostic events and re-raises startup failures. | VERIFIED | `so101_remote/server.py:64-72` records `record_exception_event(...)` then re-raises; `tests/test_minimal_async_scripts.py:211-223` proves `RuntimeError("server boom")` is re-raised and written to `events.jsonl`. |
| 9 | Client startup/control-loop records diagnostic events and re-raises runtime failures where practical. | VERIFIED | `so101_remote/client.py:127-137` records start failure and returns `1`; `so101_remote/client.py:161-169` records non-interrupt exceptions then re-raises; `tests/test_minimal_async_scripts.py:310-325` proves `RuntimeError("client boom")` is re-raised and recorded. |
| 10 | Automated tests prove artifact/reliability paths without LeRobot installed. | VERIFIED | `tests/test_minimal_async_scripts.py:78-121` installs fake LeRobot modules; all requested unittest commands passed locally without real LeRobot. |
| 11 | README and environment docs describe real runtime artifacts and the RELY-03 limitation. | VERIFIED | `README.md:64-77` documents real `policy-server` and `robot-client` artifact directories; `docs/ENVIRONMENT.md:177-203` documents `metadata.json`, `events.jsonl`, `summary.md`, resolved constants, and that RELY-03 cannot be proven by unit tests alone. |
| 12 | Phase 4 did not introduce YAML config, CLI override systems, or custom transport. | VERIFIED | Runtime modules contain no YAML/CLI parser/custom transport additions. Grep hits for YAML/CLI are documentation statements that no YAML or CLI override layer is expected; socket usage appears only in LAN connectivity documentation. |

**Score:** 12/12 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `policy_server.py` | Thin server entrypoint | VERIFIED | Imports package `HOST`, `PORT`, `build_server_config`, and `main`; no orchestration logic. |
| `robot_client.py` | Thin client entrypoint and compatibility exports | VERIFIED | Re-exports constants/helpers from `so101_remote.client`; no runtime logic beyond `SystemExit(main())`. |
| `so101_remote/server.py` | Server orchestration, official LeRobot serve, metadata, reliability hooks | VERIFIED | Substantive implementation with `server_settings`, `build_server_metadata`, `run_policy_server`, recorder use, recovery/exception events, and `serve(config)`. |
| `so101_remote/client.py` | Client orchestration, official LeRobot client, metadata, reliability hooks | VERIFIED | Substantive implementation with `client_settings`, `build_client_metadata`, `run_robot_client`, recorder use, recovery/exception events, and `RobotClient(config)`. |
| `tests/test_minimal_async_scripts.py` | Fake-LeRobot coverage for server/client artifact and reliability paths | VERIFIED | 13 focused tests cover official config objects, wrapper exports, artifacts, recovery events, and exception re-raise paths. |
| `README.md` | Operator-facing runtime artifact guidance | VERIFIED | Contains `## Real Runtime Artifacts` and names `policy-server`, `robot-client`, `metadata.json`, `events.jsonl`, `summary.md`, resolved constants, and no YAML/CLI layer. |
| `docs/ENVIRONMENT.md` | LAN readiness and artifact checks | VERIFIED | Contains `## 10-30 Minute LAN Experiment Readiness`, artifact checks, resolved constants, and RELY-03 hardware-validation boundary. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `policy_server.py` | `so101_remote.server.main()` | import and `SystemExit(main())` | WIRED | Thin entrypoint delegates runtime startup to package code. |
| `so101_remote.server.run_policy_server()` | LeRobot `serve(config)` | `_load_server_api()` and `serve(config)` | WIRED | Official transport path preserved; tests assert serve is called with `PolicyServerConfig`. |
| `so101_remote.server.run_policy_server()` | recorder/reliability artifacts | `create_run_directory`, `JsonlMetricsRecorder`, `MetricEvent`, `record_exception_event` | WIRED | Metadata/events/summary written and exception events re-raised. |
| `robot_client.py` | `so101_remote.client.main()` | imports and `SystemExit(main())` | WIRED | Thin entrypoint preserves operator-facing exports. |
| `so101_remote.client.run_robot_client()` | LeRobot `RobotClient(config)` | `build_client_config()`, `_load_client_api()`, `RobotClient(config)` | WIRED | Official client path preserved; tests assert client starts, receives actions, and runs control loop. |
| `so101_remote.client.run_robot_client()` | recorder/reliability artifacts | `create_run_directory`, `JsonlMetricsRecorder`, `MetricEvent`, `record_exception_event` | WIRED | Metadata/events/summary written; start failure and runtime exception paths are visible. |
| Documentation | Runtime artifact behavior | README and environment guide sections | WIRED | Docs name actual files and per-side run directories produced by runtime code. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `so101_remote/server.py` | `metadata` | `build_server_metadata(run_dir)` from constants plus `build_run_metadata(... current_git_commit())` | Yes | FLOWING |
| `so101_remote/server.py` | `events` | `MetricEvent(EVENT_RECOVERY, ...)` and `record_exception_event(...)` into `JsonlMetricsRecorder` | Yes | FLOWING |
| `so101_remote/client.py` | `metadata` | `build_client_metadata(run_dir)` from constants plus `build_run_metadata(... current_git_commit())` | Yes | FLOWING |
| `so101_remote/client.py` | `events` | `MetricEvent(EVENT_RECOVERY/EVENT_EXCEPTION, ...)` and `record_exception_event(...)` into `JsonlMetricsRecorder` | Yes | FLOWING |
| `README.md` / `docs/ENVIRONMENT.md` | artifact docs | Names files and run roles implemented by runtime and recorder | Yes | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Focused server/client runtime tests | `python3 -m unittest tests.test_minimal_async_scripts -v` | 13 tests passed | PASS |
| Recorder, reliability, and runtime tests | `python3 -m unittest tests.test_recorder tests.test_reliability tests.test_minimal_async_scripts -v` | 21 tests passed | PASS |
| Full test discovery | `python3 -m unittest discover -s tests -v` | 55 tests passed | PASS |
| Runtime helper symbols exist | `rg "run_policy_server|run_robot_client|server_settings|client_settings" so101_remote` | Found all four symbols | PASS |
| Docs mention artifacts and RELY-03 | `rg "Real Runtime Artifacts|10-30 Minute LAN Experiment Readiness|RELY-03" README.md docs/ENVIRONMENT.md` | Found required docs | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| RUN-01 | 04-01, 04-03 | Operator can run a LeRobot async inference policy server for SmolVLA on the GPU/server machine. | SATISFIED AUTOMATED READINESS | Thin `policy_server.py`, official `serve(config)`, and tested artifact startup path. Real GPU/model run remains human validation. |
| RUN-02 | 04-02, 04-03 | Operator can run a LeRobot async inference robot client for SO-101 on the robot-side computer. | SATISFIED AUTOMATED READINESS | Thin `robot_client.py`, official `RobotClient(config)`, and tested startup/control-loop path with fake LeRobot. Real SO-101 run remains human validation. |
| RUN-03 | 04-02, 04-03 | Robot client can configure SO-101 serial port, robot id, cameras, task text, policy type, model path, device, action chunking, aggregation, and queue debug settings. | SATISFIED | Constants in `so101_remote/config.py`; `client_settings()` and `build_client_config()` pass them through; tests verify expected config. |
| RUN-04 | 04-01, 04-02, 04-03 | Runtime path stays based on LeRobot official async inference instead of replacing it with a custom transport. | SATISFIED | Server uses official `serve(config)`; client uses official `RobotClient`; no custom transport added. |
| RUN-05 | 04-01, 04-02, 04-03 | Runtime logs startup settings sufficiently to reproduce server, robot, model, and run directory. | SATISFIED | Startup prints settings; metadata includes role, server/robot/policy fields, resolved settings, run dir, and git commit where available. |
| RELY-03 | 04-02, 04-03 | Runtime can be used for a 10-30 minute LAN experiment without expected application-level crashes. | NEEDS HUMAN | Docs provide the required 10-30 minute LAN procedure; unit tests can only prove instrumentation and exception visibility. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `so101_remote/server.py` | 85 | "not available" | INFO | User-facing missing-LeRobot runtime guidance, not a placeholder. |
| `so101_remote/client.py` | 191 | "not available" | INFO | User-facing missing-LeRobot runtime guidance, not a placeholder. |
| `docs/ENVIRONMENT.md` | 209 | "not available" | INFO | Troubleshooting documentation, not a stub. |

### Human Verification Required

### 1. RELY-03 10-30 Minute LAN Run

**Test:** On the target GPU/server machine, run `python3 policy_server.py`; on the robot-side computer, run `python3 robot_client.py`; keep the pair running for 10-30 minutes on the intended LAN.
**Expected:** No expected application-level crashes occur, and both `policy-server` and `robot-client` run directories exist under `logs/experiments/` with `metadata.json`, `events.jsonl`, and `summary.md`.
**Why human:** The repository tests intentionally fake LeRobot modules and cannot validate real SO-101 hardware, cameras, SmolVLA model loading, network behavior, or physical control-loop stability.

### Gaps Summary

No blocker gaps found in code, tests, or documentation. Automated verification proves Phase 4 readiness and instrumentation. Final RELY-03 proof still requires the documented real LAN hardware validation.

---

_Verified: 2026-05-11T04:32:11Z_
_Verifier: the agent (gsd-verifier)_
