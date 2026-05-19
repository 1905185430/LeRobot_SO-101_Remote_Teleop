# Requirements: SO-101 Remote VLA Inference Experiments

**Defined:** 2026-05-11
**Core Value:** SO-101 + SmolVLA remote inference must run stably while producing trustworthy communication metrics that can be used for wireless communication experiments.

## v1 Requirements

Requirements for the first practical release. v1 is intentionally layered: the core run path must work, while reporting, recovery, adapters, and configuration can be lightweight.

### Structure

- [x] **STRC-01**: Developer can import a small `so101_remote/` package containing runtime, metrics, recorder, adapter, and dry-run modules.
- [x] **STRC-02**: Operator can still start the server through `policy_server.py`, with the script acting as a thin entrypoint.
- [x] **STRC-03**: Operator can still start the robot client through `robot_client.py`, with the script acting as a thin entrypoint.
- [x] **STRC-04**: Existing legacy teleoperation code remains under `legacy/` and is not broken by the package restructure.

### Inference Runtime

- [ ] **RUN-01**: Operator can run a LeRobot async inference policy server for SmolVLA on the GPU/server machine.
- [ ] **RUN-02**: Operator can run a LeRobot async inference robot client for SO-101 on the robot-side computer.
- [ ] **RUN-03**: Robot client can configure SO-101 serial port, robot id, cameras, task text, policy type, model path, device, action chunking, aggregation, and queue debug settings.
- [ ] **RUN-04**: Runtime path stays based on LeRobot official async inference instead of replacing it with a custom transport.
- [ ] **RUN-05**: Runtime logs startup settings sufficiently to reproduce which server, robot, model, and run directory were used.

### Metrics

- [x] **METR-01**: Runtime records latency-related samples when timestamps or LeRobot hooks expose enough signal.
- [x] **METR-02**: Runtime records RTT or RTT-like measurements where request/response or heartbeat timing is available.
- [x] **METR-03**: Runtime derives jitter from recorded latency or interval samples.
- [x] **METR-04**: Runtime records timeout, disconnect, retry, recovery, and exception events.
- [x] **METR-05**: Runtime records control-loop frequency or loop interval samples.
- [x] **METR-06**: Runtime records action chunk arrival intervals when action chunks are received.
- [x] **METR-07**: Runtime records queue state or queue size when LeRobot exposes it.
- [x] **METR-08**: Operator can see a readable terminal metrics summary during a run.
- [x] **METR-09**: Metrics are saved locally as JSONL and/or CSV.

### Experiments

- [x] **EXP-01**: Each experiment run writes outputs under a local `runs/` or `logs/experiments/` directory.
- [x] **EXP-02**: Each run has a unique run directory.
- [x] **EXP-03**: Each run directory includes run metadata that identifies timestamp, role, model/policy settings, robot settings, network endpoint, and git commit when available.
- [x] **EXP-04**: Each run directory includes structured metrics files.
- [x] **EXP-05**: Each run can produce a lightweight Markdown summary with basic statistics such as count, min, max, mean, and p95 for key metrics.

### Dry Run

- [x] **DRY-01**: Developer can run a dry-run/mock mode on one machine without SO-101 hardware.
- [x] **DRY-02**: Dry-run mode exercises the runtime and metrics recorder enough to validate log and run-directory behavior.
- [x] **DRY-03**: Dry-run mode does not pretend to validate real hardware, camera, model loading, or physical control behavior.

### Adapters

- [x] **ADPT-01**: Code defines a minimal robot adapter boundary sufficient to isolate SO-101-specific setup from runtime orchestration.
- [x] **ADPT-02**: Code defines a minimal policy/model adapter boundary sufficient to keep SmolVLA-specific setup from blocking later PI-series support.
- [x] **ADPT-03**: SO-101 + SmolVLA is implemented as the first concrete path without requiring a heavy plugin registry.
- [x] **ADPT-04**: PI-series model support has a clear placeholder or extension point, but no real PI backend is required in early v1.
- [x] **ADPT-05**: Other robot arm support has a clear placeholder or extension point, but no second hardware backend is required in early v1.

### Reliability

- [x] **RELY-01**: Runtime records errors with enough context to diagnose server startup, client startup, LeRobot import, model path, camera, serial port, network, and timeout failures.
- [x] **RELY-02**: Runtime includes simple retry or recovery behavior where practical without a complex state machine.
- [ ] **RELY-03**: Runtime can be used for a 10-30 minute LAN experiment without expected application-level crashes.
- [x] **RELY-04**: Existing unit tests continue to pass after the package restructure.
- [x] **RELY-05**: Legacy teleoperation tests continue to pass so retained compatibility is protected.

### Documentation

- [x] **DOC-01**: Project includes an environment setup guide under `docs/`.
- [x] **DOC-02**: Environment guide covers GPU/server machine setup, including Python, LeRobot, CUDA/PyTorch checks, SmolVLA model path, HuggingFace access, and policy server preflight checks.
- [x] **DOC-03**: Environment guide covers robot-side setup, including LeRobot, SO-101 serial permissions, follower calibration id, cameras, and robot client preflight checks.
- [x] **DOC-04**: Environment guide covers LAN communication checks, including server IP/port, firewall, ping/basic connectivity, and time synchronization guidance for trustworthy metrics.
- [x] **DOC-05**: Environment guide covers dry-run/mock operation.
- [x] **DOC-06**: Environment guide covers common failures: LeRobot import failure, CUDA unavailable, invalid model path, camera index mismatch, serial port permission failure, server connection failure, and metrics output confusion.

### Configuration

- [x] **CONF-01**: v1 can keep script-level constants as the primary configuration path.
- [x] **CONF-02**: Code structure leaves a future path for CLI or YAML overrides without making that a blocker for the first working release.
- [x] **CONF-03**: Operator-facing constants are documented clearly enough to edit before a real run.

## v2 Requirements

Deferred to future releases. These are in the project roadmap but should not block the first practical v1.

### Teleoperation

- **TELE-01**: Legacy teleoperation can be integrated into the new runtime/metrics framework.
- **TELE-02**: Teleoperation and model inference can be compared under shared metrics.
- **TELE-03**: Teleoperation can optionally support fallback/manual override workflows if needed later.
- **TELE-04**: Wireless teleoperation integration can be planned as a first-class experiment mode without replacing the v1 LeRobot async inference path.

### Reporting

- **RPT-01**: Experiment reports can include charts or time-series plots.
- **RPT-02**: Multiple runs can be compared in a single summary.
- **RPT-03**: Reports can separate server-side, client-side, and end-to-end metrics clearly.

### Configuration

- **CFG-01**: Runtime can load YAML configuration files.
- **CFG-02**: CLI arguments can override YAML or default settings.
- **CFG-03**: Config files can be saved into each run directory for reproducibility.

### Integrations

- **PI-01**: PI-series policy adapter is implemented and validated with at least one real PI model path.
- **ROBOT-01**: A second robot arm adapter is implemented and validated.
- **ROBOT-02**: Multi-arm support can select and describe multiple robot arm types without turning v1 into a heavy plugin platform.
- **VLA-01**: VLA inference expansion beyond the first SmolVLA path can be planned and validated independently of wireless teleoperation work.
- **NET-01**: Non-LAN deployment guidance is added for VPN or cross-network experiments.

### Validation Documentation

- **VAL-01**: Validation documentation separates `unit-only`, `dry-run-only`, `real LeRobot required`, `hardware-required`, and `10-30 min LAN required` checks.
- **VAL-02**: Validation documentation keeps real LAN/hardware UAT pending unless it has actually been performed.

### Dataset TCP Replay

- **DATASET-TCP-01**: Operator can select an existing LeRobot SO-101 dataset from YAML by local dataset path.
- **DATASET-TCP-02**: Runtime can replay selected dataset episode actions through the TCP teleoperation client path instead of reading a physical leader arm.
- **DATASET-TCP-03**: Local baseline uses one machine and `127.0.0.1` TCP first; two-machine remote TCP replay is a follow-up phase.
- **DATASET-TCP-04**: Replay validates SO-101 action keys, value ranges, first-action delta, and per-frame delta limits with the existing teleoperation safety model.
- **DATASET-TCP-05**: Replay run artifacts record dataset path, selected episode ids, frame count, replay frequency, TCP endpoint, safety settings, and any skipped/failed frames.
- **DATASET-TCP-06**: Replay provides a hardware-free validation path using fake dataset/fake follower data so parsing, TCP send, metrics, and artifact generation can be tested before real SO-101 runs.
- **DATASET-TCP-07**: Documentation explains local dataset replay prerequisites, YAML fields, startup order, validation commands, and boundaries versus dataset collection and remote two-machine replay.

## Out of Scope

Explicitly excluded from the initial roadmap.

| Feature | Reason |
|---------|--------|
| Dashboard UI | The first priority is stable remote inference and structured metrics, not visualization infrastructure. |
| Heavy plugin registry | Minimal adapter boundaries are enough for expected PI/robot extensions. |
| Replacing LeRobot async inference transport | The project should use the official path first and measure around it. |
| Full hardware safety controller | Important for production robotics, but this project is scoped to experiment runtime and communication metrics. |
| Public internet deployment as v1 target | v1 is for GPU server plus robot-side computer on the same LAN. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| STRC-01 | Phase 1 | Complete |
| STRC-02 | Phase 1 | Complete |
| STRC-03 | Phase 1 | Complete |
| STRC-04 | Phase 1 | Complete |
| RUN-01 | Phase 4 | Pending |
| RUN-02 | Phase 4 | Pending |
| RUN-03 | Phase 4 | Pending |
| RUN-04 | Phase 4 | Pending |
| RUN-05 | Phase 4 | Pending |
| METR-01 | Phase 2 | Complete |
| METR-02 | Phase 2 | Complete |
| METR-03 | Phase 2 | Complete |
| METR-04 | Phase 2 | Complete |
| METR-05 | Phase 2 | Complete |
| METR-06 | Phase 2 | Complete |
| METR-07 | Phase 2 | Complete |
| METR-08 | Phase 2 | Complete |
| METR-09 | Phase 2 | Complete |
| EXP-01 | Phase 2 | Complete |
| EXP-02 | Phase 2 | Complete |
| EXP-03 | Phase 2 | Complete |
| EXP-04 | Phase 2 | Complete |
| EXP-05 | Phase 2 | Complete |
| DRY-01 | Phase 3 | Complete |
| DRY-02 | Phase 3 | Complete |
| DRY-03 | Phase 3 | Complete |
| ADPT-01 | Phase 3 | Complete |
| ADPT-02 | Phase 3 | Complete |
| ADPT-03 | Phase 3 | Complete |
| ADPT-04 | Phase 3 | Complete |
| ADPT-05 | Phase 3 | Complete |
| RELY-01 | Phase 3 | Complete |
| RELY-02 | Phase 3 | Complete |
| RELY-03 | Phase 4 | Pending |
| RELY-04 | Phase 5 | Complete |
| RELY-05 | Phase 5 | Complete |
| DOC-01 | Phase 1 | Complete |
| DOC-02 | Phase 1 | Complete |
| DOC-03 | Phase 1 | Complete |
| DOC-04 | Phase 1 | Complete |
| DOC-05 | Phase 1 | Complete |
| DOC-06 | Phase 1 | Complete |
| CONF-01 | Phase 1 | Complete |
| CONF-02 | Phase 1 | Complete |
| CONF-03 | Phase 1 | Complete |
| DATASET-TCP-01 | Phase 7 | Pending |
| DATASET-TCP-02 | Phase 7 | Pending |
| DATASET-TCP-03 | Phase 7 | Pending |
| DATASET-TCP-04 | Phase 7 | Pending |
| DATASET-TCP-05 | Phase 7 | Pending |
| DATASET-TCP-06 | Phase 7 | Pending |
| DATASET-TCP-07 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 44 total
- Dataset TCP replay requirements: 7 total
- Mapped to phases: 51
- Unmapped: 0

---
*Requirements defined: 2026-05-11*
*Last updated: 2026-05-19 after Phase 7 dataset TCP replay specification*
