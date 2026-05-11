# Phase 4: SO-101 SmolVLA Runtime Integration - Context

**Gathered:** 2026-05-11T04:00:13Z
**Status:** Ready for planning

<domain>
## Phase Boundary

Route the real LeRobot async inference policy server and SO-101 robot client through the `so101_remote` package while preserving the official LeRobot transport path and the thin top-level entrypoints. This phase should make real server/client startup reproducible through run metadata, resolved settings, logs, and reliability events, without introducing YAML/CLI configuration or replacing LeRobot async inference.

</domain>

<decisions>
## Implementation Decisions

### Runtime Boundaries
- **D-01:** Use lightweight orchestration helpers, not a large runtime platform. Planning should introduce helpers such as `run_policy_server()` and `run_robot_client()` or equivalent package-level functions that coordinate config construction, metadata, recorder setup, reliability events, and LeRobot startup.
- **D-02:** Preserve `policy_server.py` and `robot_client.py` as thin entrypoints. They should continue to import from `so101_remote` and delegate to package code.
- **D-03:** Do not introduce long-lived runtime classes unless research shows they remove real complexity. The preferred shape is small functions around the existing LeRobot config factories and startup calls.

### Run Artifacts
- **D-04:** Server and robot client should each create their own run directory for v1.
- **D-05:** Do not require shared run IDs or cross-machine run-directory synchronization in this phase. If a correlation field is cheap, it may be stored, but it must not become a blocker.
- **D-06:** Each side's metadata should include enough overlapping context to correlate runs manually: role, endpoint, model/policy fields, robot fields where known, resolved constants, run directory, and git commit when available.

### Failure Handling
- **D-07:** Apply reliability hooks to both startup and connection-oriented operations.
- **D-08:** Reliability hooks must record diagnostic events but must not swallow hardware/runtime failures. Exceptions should remain visible to operators after being recorded.
- **D-09:** Bounded retry is allowed only where it is practical and safe, such as transient server/client connection setup. Do not retry robot action execution or hide control-loop failures.

### Operator Constants And Logs
- **D-10:** Keep script/package constants as the primary v1 configuration surface.
- **D-11:** Add a small helper or helpers that produce resolved settings for server and client startup.
- **D-12:** Resolved settings should be printed at startup and saved into run metadata. Do not add YAML loading or broad CLI override support in Phase 4.

### the agent's Discretion
- The planner may choose exact helper names and file placement if they preserve the lightweight package shape and thin entrypoints.
- The planner may decide which LeRobot operations can be safely wrapped with `run_with_retries()` after inspecting the current client/server control flow.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Scope And Requirements
- `.planning/ROADMAP.md` — Phase 4 goal, requirements, success criteria, and planned slices.
- `.planning/REQUIREMENTS.md` — RUN-01 through RUN-05 and RELY-03 traceability.
- `.planning/PROJECT.md` — project constraints: LeRobot official path, LAN target, constants accepted for v1, metrics as first-class output.
- `.planning/STATE.md` — current status and decisions carried from Phase 03.

### Existing Runtime Code
- `policy_server.py` — top-level server entrypoint that must stay thin.
- `robot_client.py` — top-level robot client entrypoint that must stay thin and preserve exported constants/helpers for tests.
- `so101_remote/server.py` — current LeRobot policy server config factory and startup function.
- `so101_remote/client.py` — current LeRobot robot client config factories, lazy imports, receiver thread, and control-loop startup.
- `so101_remote/config.py` — current v1 constants that remain the main configuration surface.

### Artifact, Metrics, And Reliability Foundations
- `so101_remote/recorder.py` — run directory, metadata, JSONL/CSV recorder, and summary helpers.
- `so101_remote/metrics.py` — metric sample/event models and terminal summary helper.
- `so101_remote/reliability.py` — exception, retry, and recovery event helpers to reuse around startup/connection behavior.
- `so101_remote/dryrun.py` — deterministic example of recorder + reliability event plumbing in one run artifact set.

### Adapter And Documentation Context
- `so101_remote/adapters/lerobot_so101.py` — SO-101 and SmolVLA adapter locations created in Phase 03.
- `docs/ENVIRONMENT.md` — operator setup assumptions for GPU/server, robot-side machine, LAN checks, model path, cameras, serial permissions, and common failures.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `build_run_metadata()` and `create_run_directory()` can create per-role server/client run directories and metadata.
- `JsonlMetricsRecorder` can write startup, retry, recovery, and exception events to `events.jsonl`.
- `record_exception_event()` and `run_with_retries()` are the approved reliability primitives for diagnostic recording and bounded retry.
- `so101_remote.config` centralizes v1 constants that should be printed and persisted as resolved settings.

### Established Patterns
- LeRobot imports are lazy so unit tests and static inspection can run without LeRobot installed.
- Top-level scripts are thin wrappers guarded by `if __name__ == "__main__"`.
- Tests use fake modules in `sys.modules` rather than requiring LeRobot or hardware.
- The project prefers small helper functions and dataclasses/protocols over plugin registries or platform abstractions.

### Integration Points
- Server startup currently flows through `so101_remote.server.main()` -> `build_server_config()` -> LeRobot `serve(config)`.
- Robot startup currently flows through `so101_remote.client.main()` -> `build_client_config()` -> `RobotClient.start()` -> daemon `receive_actions` thread -> `control_loop(TASK)`.
- Real runtime metadata should connect to existing constants: host/port, server address, robot serial/id, cameras, task text, policy type/model path/device, action chunking, aggregation, and queue visualization flag.

</code_context>

<specifics>
## Specific Ideas

- Preferred implementation shape: lightweight orchestration helpers, not a runtime class hierarchy.
- Server and client should each have their own run directory for v1.
- Record startup and connection failures as reliability events, then re-raise.
- Keep constants as configuration, but print and save resolved settings before startup.

</specifics>

<deferred>
## Deferred Ideas

- Shared cross-machine run IDs or coordinated server/client artifact merging can wait for a future reporting/configuration phase.
- YAML config and CLI override systems remain deferred v2-style improvements unless a tiny helper is required for testability.
- Retrying robot action execution or masking control-loop failures is out of scope for Phase 4.

</deferred>

---

*Phase: 4-SO-101 SmolVLA Runtime Integration*
*Context gathered: 2026-05-11T04:00:13Z*
