# Phase 7: SO-101 Local TCP Dataset Replay Baseline - Context

**Gathered:** 2026-05-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 7 builds a LeRobot-compatible local TCP dataset replay baseline for SO-101. It consumes an existing local LeRobot dataset path, replays one selected episode's action frames through this project's TCP client/server path on `127.0.0.1`, preserves the existing teleoperation safety checks, and records run artifacts proving what was replayed.

</domain>

<spec_lock>
## Requirements (locked via SPEC.md)

**7 requirements are locked.** See `07-SPEC.md` for full requirements, boundaries, and acceptance criteria.

Downstream agents MUST read `07-SPEC.md` before planning or implementing. Requirements are not duplicated here.

**In scope (from SPEC.md):**
- A local dataset replay phase for SO-101 only.
- YAML-selectable local LeRobot dataset path.
- Episode/frame selection and replay timing controls sufficient for local experiments.
- Dataset action extraction into SO-101 six-joint action messages.
- Local TCP replay client behavior compatible with the existing follower server.
- Existing safety checks and run artifacts applied to dataset replay.
- Fake dataset/fake follower tests that do not require hardware or network access.
- Operator documentation for local dataset replay.

**Out of scope (from SPEC.md):**
- Collecting LeRobot datasets — the operator can use LeRobot commands separately.
- Automatic HuggingFace dataset download — datasets may be downloaded beforehand and referenced by path.
- Two-machine remote TCP dataset replay — deferred to the next phase after local replay is proven.
- VLA inference, policy evaluation, or model training on the replayed dataset — separate experiment class.
- Retargeting arbitrary non-SO-101 datasets — this phase expects SO-101-compatible action dimensions/keys.
- Camera/video replay to robot hardware — this phase replays robot action trajectories; observations/images may be inspected for metadata but are not sent as robot commands.
- Weakening or bypassing teleoperation safety limits to force a dataset to replay.

</spec_lock>

<decisions>
## Implementation Decisions

### LeRobot Replay Relationship
- **D-01:** Treat official `python -m lerobot.replay` as a required reference/preflight path, not as the Phase 7 implementation.
- **D-02:** Documentation should instruct operators to use official LeRobot replay first to verify that the dataset, episode, follower hardware, calibration, and local direct-control replay are sane before testing this project's TCP replay path.
- **D-03:** Implement a project-owned TCP dataset replay client that sends dataset actions through this repository's TCP protocol and follower server.
- **D-04:** Reuse LeRobot's dataset-reading capability through a small adapter boundary. Do not depend on `lerobot.replay` internal control-flow implementation unless research proves there is a stable public API for the needed episode/action iteration.

### YAML Configuration Shape
- **D-05:** Add a `dataset:` config section using simple scalar fields compatible with the current YAML parser.
- **D-06:** The first YAML shape should support a single episode:
  - `dataset.path`
  - `dataset.episode`
  - `dataset.start_frame`
  - `dataset.end_frame`
  - `dataset.timing`
  - `dataset.replay_frequency`
- **D-07:** Do not extend the YAML parser for lists in Phase 7 just to support multi-episode replay.
- **D-08:** Missing `dataset.path` or an invalid dataset path must fail before sending any TCP action.

### Replay Timing
- **D-09:** Support both `fixed_hz` and `source_timestamps` timing modes in the config surface.
- **D-10:** `fixed_hz` is the default, primary, and required acceptance path for Phase 7.
- **D-11:** `source_timestamps` may be supported only when the dataset exposes clear timestamp/fps information. If not available, the runtime must fail clearly instead of silently falling back.
- **D-12:** Run artifacts must record the selected timing mode and either the replay frequency or the source timing metadata used.

### Safety Failure Behavior
- **D-13:** Use fail-fast behavior as the Phase 7 default for safety and transport failures.
- **D-14:** Invalid action keys, action range violations, first-action delta failures, TCP ACK mismatch, timeouts, connection errors, and dataset read failures must abort the current replay episode.
- **D-15:** Do not skip bad frames, silently clamp dataset actions to keep replay going, or add pause/continue operator interaction in Phase 7.
- **D-16:** All aborts must be recorded in `events.jsonl` and summarized in `summary.md`.
- **D-17:** If the follower server's existing per-frame delta limiter triggers, record that event clearly so a replay that diverges from dataset trajectory is not mistaken for a clean reproduction.

### Script Entry And Operator Flow
- **D-18:** Add a dedicated dataset replay client script rather than overloading `run_teleop_leader.py`.
- **D-19:** Preferred command shape:
  - `python3 scripts/run_dataset_replay_client.py --config configs/replay/local_so101_tcp_dataset.yaml`
- **D-20:** Follower/server should continue to use the role-explicit follower entrypoint:
  - `python3 scripts/run_teleop_follower.py --config configs/replay/local_so101_tcp_dataset.yaml`
- **D-21:** Do not introduce a broader `run_action_client.py` / generalized `ActionSource -> Transport -> ActionSink` command in Phase 7. That architecture may emerge later, but Phase 7 should stay focused on dataset replay.

### the agent's Discretion
- The planner may choose exact module names under `lerobot_remote/` for dataset replay internals if they preserve the locked boundaries above.
- The planner may decide whether the dataset action source adapter lives under `lerobot_remote/datasets/`, `lerobot_remote/replay/`, or a similarly focused package.
- The planner may choose the exact fake dataset fixture format for tests as long as it does not require hardware, HuggingFace network access, or a real LeRobot dataset.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Locked Phase Requirements
- `.planning/phases/07-so101-local-tcp-dataset-replay-baseline/07-SPEC.md` — Locked Phase 7 requirements, boundaries, constraints, and acceptance criteria.
- `.planning/ROADMAP.md` — Phase 7 roadmap entry and dependency on Phase 6.
- `.planning/REQUIREMENTS.md` — DATASET-TCP requirement traceability.

### Existing SO-101 TCP Behavior
- `docs/reproduction/SO101_LOCAL_TCP_TELEOP.md` — Validated local TCP operator flow, ports, safety settings, and artifacts.
- `docs/reproduction/SO101_WIRELESS_TCP_TELEOP.md` — Existing remote TCP reproduction context for future Phase 8, explicitly not Phase 7 scope.
- `configs/teleop/local_so101_tcp.yaml` — Current local SO-101 TCP config shape and safety defaults.

### Relevant Runtime Code
- `lerobot_remote/teleop/client.py` — Existing live leader TCP client pattern to adapt or reuse carefully.
- `lerobot_remote/teleop/server.py` — Existing follower TCP server, safety baseline, ACK handling, timeout behavior.
- `lerobot_remote/runtime/teleoperation.py` — Role-explicit runtime orchestration and run artifact pattern.
- `lerobot_remote/config/schema.py` — Current config schema and validation surface; no dataset section yet.
- `lerobot_remote/config/loader.py` — Current simple YAML parser constraints.
- `lerobot_remote/recording/recorder.py` — Run artifact writer and summary generation.

### External Baseline
- Hugging Face LeRobot official docs, "Replay an episode" command (`python -m lerobot.replay`) — Use as operator preflight/reference for dataset/follower sanity, not as the internal implementation contract.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TcpTeleopFollowerServer`: already receives ACTION messages, validates ordering, enforces first-action and per-frame safety, sends ACKs, records metrics/events, and updates dashboard state.
- `TcpTeleopLeaderClient`: already has socket send/ACK loop, frame sequencing, RTT metric recording, action printing, and state updates. Its current `leader_device.get_action()` source is live-device-specific.
- `normalize_teleop_action` and `validate_action_values`: reusable for dataset-sourced action normalization and validation.
- `JsonlMetricsRecorder` and runtime common helpers: reusable for replay metadata, config copy, metrics, events, and summaries.

### Established Patterns
- Runtime entrypoints are role-explicit scripts under `scripts/` with `--config` and `--dry-run`.
- Config-driven modes use YAML under typed subdirectories and structured dataclasses in `lerobot_remote/config/schema.py`.
- Hardware-facing failures should be visible and re-raised; recording events must not silently hide failures.
- Tests use fake LeRobot modules and fake devices to avoid requiring hardware or external services.

### Integration Points
- Add a dataset replay config section to `PlatformConfig` and loader validation.
- Add a dedicated dataset replay client runtime parallel to `run_tcp_teleop_leader_client`, but sourcing actions from dataset frames instead of a physical leader.
- Add `configs/replay/local_so101_tcp_dataset.yaml` or equivalent path for the local baseline.
- Add `scripts/run_dataset_replay_client.py` as the dataset replay entrypoint.
- Reuse `scripts/run_teleop_follower.py` for the follower/server side.

</code_context>

<specifics>
## Specific Ideas

- The first concrete operator flow should be:
  1. Optionally run official `python -m lerobot.replay` to prove dataset/follower sanity.
  2. Start the local TCP follower/server with the dataset replay YAML.
  3. Start the dedicated dataset replay client with the same YAML.
- The default dataset timing should be `fixed_hz`, likely using `dataset.replay_frequency` and falling back to `runtime.action_send_frequency` only if the planner decides that fallback keeps config clearer.
- The dataset path is local. Operators may create it with LeRobot commands or download/cache it from HuggingFace beforehand.

</specifics>

<deferred>
## Deferred Ideas

- Multi-episode batch replay — useful later, but Phase 7 starts with one episode to avoid YAML parser/list complexity.
- Remote two-machine TCP dataset replay — belongs after the local TCP baseline is proven.
- Interactive pause/continue on safety failure — useful for hardware operation polish, but Phase 7 uses fail-fast behavior.
- Generalized `ActionSource -> Transport -> ActionSink` command/API — a promising later architecture once dataset replay proves the shape.
- Automatic HuggingFace dataset download — deferred; Phase 7 consumes a local dataset path.

</deferred>

---

*Phase: 7-SO-101 Local TCP Dataset Replay Baseline*
*Context gathered: 2026-05-19*
