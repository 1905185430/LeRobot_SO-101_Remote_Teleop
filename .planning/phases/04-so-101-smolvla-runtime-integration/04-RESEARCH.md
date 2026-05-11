---
phase: 04-so-101-smolvla-runtime-integration
focus: implementation-research
status: complete
created: 2026-05-11
requirements: [RUN-01, RUN-02, RUN-03, RUN-04, RUN-05, RELY-03]
---

# Phase 04 Research: SO-101 SmolVLA Runtime Integration

## Research Question

What needs to be known to plan Phase 04 well: routing the real LeRobot async inference server and SO-101 client through `so101_remote`, while preserving official LeRobot transport, thin entrypoints, constant-based configuration, run artifacts, and reliability diagnostics?

## Current Runtime Shape

- `policy_server.py` and `robot_client.py` are already thin top-level wrappers.
- `so101_remote.server` builds `PolicyServerConfig(host=HOST, port=PORT)` and calls LeRobot `serve(config)`.
- `so101_remote.client` builds camera, SO-101 follower, and `RobotClientConfig`, then starts `RobotClient`, spawns `receive_actions`, and runs `control_loop(TASK)`.
- LeRobot imports are lazy and tests stub only the imported modules in `sys.modules`.
- `so101_remote.config` is the accepted v1 configuration surface and should remain constant-based.

## Prior Phase Assets To Reuse

- `so101_remote.recorder.create_run_directory()` creates local per-role run directories.
- `so101_remote.recorder.build_run_metadata()` already supports server, robot, policy, extra fields, and git commit.
- `JsonlMetricsRecorder` can write metadata, events, metrics, CSV, and summary files.
- `so101_remote.reliability.record_exception_event()` records structured exception diagnostics.
- `so101_remote.reliability.run_with_retries()` records retry/recovery events and re-raises final failures.
- `so101_remote.dryrun.run_dry_run()` is the reference for deterministic recorder + reliability event plumbing.

## Implementation Guidance

### 1. Add resolved settings helpers before orchestration

Plan server/client settings helpers first. They should return plain dictionaries, not LeRobot config objects:

- `server_settings()` should include at least `host`, `port`, and `endpoint`.
- `client_settings()` should include `server_address`, `robot_port`, `robot_id`, `cameras`, `task`, `policy_type`, `pretrained_name_or_path`, `policy_device`, `actions_per_chunk`, `chunk_size_threshold`, `aggregate_fn_name`, and `debug_visualize_queue_size`.
- A formatting helper can produce stable startup text. Tests should assert exact keys and important values.

This isolates reproducibility metadata from LeRobot object internals and lets tests run without LeRobot installed.

### 2. Add lightweight orchestration, not runtime classes

Preferred helper shape:

- `run_policy_server()` in `so101_remote.server`
- `run_robot_client()` in `so101_remote.client`

`main()` should call those helpers and return their exit code. Top-level wrappers should stay unchanged except for imports if needed.

Avoid long-lived runtime classes for Phase 04 unless a later executor finds concrete complexity that functions cannot handle. This matches the locked context decisions and keeps v1 lightweight.

### 3. Server and client each own a run directory

Server metadata should include:

- `role: "policy-server"`
- server host/port/endpoint
- policy type, model path, and policy device when known from constants
- resolved settings in `extra`

Client metadata should include:

- `role: "robot-client"`
- server address
- robot id and serial port
- cameras
- policy type, model path, policy device
- action chunking and aggregation settings
- resolved settings in `extra`

Do not require a shared run id. If a cheap correlation value is added, it must not require cross-machine coordination.

### 4. Reliability hooks should record and re-raise

Wrap startup/config operations so failures are written to `events.jsonl`, then re-raised:

- Server: LeRobot import/config construction/serve startup.
- Client: LeRobot import/config construction/robot client construction/start, receive thread setup, and control-loop startup boundary.

Use `run_with_retries()` only around operations that are safe to retry. `RobotClient.start()` may be wrapped if tests show the fake client can model a failed first start, but action execution/control-loop operations should not be retried automatically.

Do not convert exceptions into silent exit codes except where current behavior intentionally returns `1` for `client.start() == False`. Even then, record a diagnostic event before returning.

### 5. Metrics hooks should be minimal in this phase

Phase 04 should ensure the real runtime writes artifact sets and event diagnostics. It should not overpromise deep latency/action queue metrics if LeRobot does not expose the signals yet.

Safe additions:

- startup/recovery/exception events
- run metadata
- terminal settings printout
- summary write on graceful client/server exit where reachable
- queue visualization on KeyboardInterrupt remains preserved

Detailed latency and queue sampling can remain limited to what current code can safely observe.

## Validation Architecture

### Automated Unit Coverage

- Server settings helper returns expected constant-derived dictionary.
- Client settings helper returns expected constant-derived dictionary including camera and action settings.
- Server orchestration creates a recorder/run directory, writes metadata, calls LeRobot `serve(config)`, and records startup/recovery event(s).
- Server orchestration records an exception event and re-raises on `serve()` failure.
- Client orchestration creates a recorder/run directory, writes metadata, starts fake `RobotClient`, starts the receive thread, and runs `control_loop(TASK)`.
- Client orchestration records exception events and re-raises for construction/startup/control-loop failures where appropriate.
- Existing thin wrapper tests keep passing.

### Integration/Behavior Checks

- `python3 -m unittest tests.test_minimal_async_scripts -v`
- `python3 -m unittest tests.test_recorder tests.test_reliability tests.test_minimal_async_scripts -v`
- `python3 -m unittest discover -s tests -v`
- Grep checks for new public helpers: `run_policy_server`, `run_robot_client`, `server_settings`, `client_settings`.

### Human/Hardware Validation

RELY-03 cannot be fully proven by unit tests. Phase 04 should create a plan task or verification note for a 10-30 minute LAN experiment readiness check using real LeRobot environments. The plan should clearly distinguish automated readiness from physical hardware validation.

## Planning Recommendation

Use three plans in dependency order:

1. Server orchestration and artifacts.
2. Client orchestration and artifacts.
3. Cross-runtime readiness, documentation/tests, and 10-30 minute LAN experiment checklist.

This matches the existing roadmap slices and keeps server/client work separable while allowing the final plan to verify the real experiment story end-to-end.

## Risks And Mitigations

- **LeRobot unavailable in tests:** preserve lazy imports and fake module stubs.
- **Recorder not closed on exception:** use context managers around recorder setup where possible; if `serve()` blocks indefinitely, summary writing may only happen on graceful exception/interrupt paths.
- **Over-retrying hardware operations:** restrict retries to startup/connection boundaries and re-raise final failures.
- **Run artifact claims exceed actual signals:** metadata and event artifacts are required; deeper latency/queue samples should be added only where signals are available.
- **Top-level wrapper compatibility breaks:** keep existing exports and tests in `tests/test_minimal_async_scripts.py`.

## RESEARCH COMPLETE
