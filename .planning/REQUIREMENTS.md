# Requirements: SO-101 Remote VLA Inference Experiments

**Defined:** 2026-05-11
**Core Value:** SO-101 + SmolVLA remote inference must run stably while producing trustworthy communication metrics that can be used for wireless communication experiments.

## v1 Requirements

Requirements for the first practical release. v1 is intentionally layered: the core run path must work, while reporting, recovery, adapters, and configuration can be lightweight.

### Structure

- [ ] **STRC-01**: Developer can import a small `so101_remote/` package containing runtime, metrics, recorder, adapter, and dry-run modules.
- [ ] **STRC-02**: Operator can still start the server through `policy_server.py`, with the script acting as a thin entrypoint.
- [ ] **STRC-03**: Operator can still start the robot client through `robot_client.py`, with the script acting as a thin entrypoint.
- [ ] **STRC-04**: Existing legacy teleoperation code remains under `legacy/` and is not broken by the package restructure.

### Inference Runtime

- [ ] **RUN-01**: Operator can run a LeRobot async inference policy server for SmolVLA on the GPU/server machine.
- [ ] **RUN-02**: Operator can run a LeRobot async inference robot client for SO-101 on the robot-side computer.
- [ ] **RUN-03**: Robot client can configure SO-101 serial port, robot id, cameras, task text, policy type, model path, device, action chunking, aggregation, and queue debug settings.
- [ ] **RUN-04**: Runtime path stays based on LeRobot official async inference instead of replacing it with a custom transport.
- [ ] **RUN-05**: Runtime logs startup settings sufficiently to reproduce which server, robot, model, and run directory were used.

### Metrics

- [ ] **METR-01**: Runtime records latency-related samples when timestamps or LeRobot hooks expose enough signal.
- [ ] **METR-02**: Runtime records RTT or RTT-like measurements where request/response or heartbeat timing is available.
- [ ] **METR-03**: Runtime derives jitter from recorded latency or interval samples.
- [ ] **METR-04**: Runtime records timeout, disconnect, retry, recovery, and exception events.
- [ ] **METR-05**: Runtime records control-loop frequency or loop interval samples.
- [ ] **METR-06**: Runtime records action chunk arrival intervals when action chunks are received.
- [ ] **METR-07**: Runtime records queue state or queue size when LeRobot exposes it.
- [ ] **METR-08**: Operator can see a readable terminal metrics summary during a run.
- [ ] **METR-09**: Metrics are saved locally as JSONL and/or CSV.

### Experiments

- [ ] **EXP-01**: Each experiment run writes outputs under a local `runs/` or `logs/experiments/` directory.
- [ ] **EXP-02**: Each run has a unique run directory.
- [ ] **EXP-03**: Each run directory includes run metadata that identifies timestamp, role, model/policy settings, robot settings, network endpoint, and git commit when available.
- [ ] **EXP-04**: Each run directory includes structured metrics files.
- [ ] **EXP-05**: Each run can produce a lightweight Markdown summary with basic statistics such as count, min, max, mean, and p95 for key metrics.

### Dry Run

- [ ] **DRY-01**: Developer can run a dry-run/mock mode on one machine without SO-101 hardware.
- [ ] **DRY-02**: Dry-run mode exercises the runtime and metrics recorder enough to validate log and run-directory behavior.
- [ ] **DRY-03**: Dry-run mode does not pretend to validate real hardware, camera, model loading, or physical control behavior.

### Adapters

- [ ] **ADPT-01**: Code defines a minimal robot adapter boundary sufficient to isolate SO-101-specific setup from runtime orchestration.
- [ ] **ADPT-02**: Code defines a minimal policy/model adapter boundary sufficient to keep SmolVLA-specific setup from blocking later PI-series support.
- [ ] **ADPT-03**: SO-101 + SmolVLA is implemented as the first concrete path without requiring a heavy plugin registry.
- [ ] **ADPT-04**: PI-series model support has a clear placeholder or extension point, but no real PI backend is required in early v1.
- [ ] **ADPT-05**: Other robot arm support has a clear placeholder or extension point, but no second hardware backend is required in early v1.

### Reliability

- [ ] **RELY-01**: Runtime records errors with enough context to diagnose server startup, client startup, LeRobot import, model path, camera, serial port, network, and timeout failures.
- [ ] **RELY-02**: Runtime includes simple retry or recovery behavior where practical without a complex state machine.
- [ ] **RELY-03**: Runtime can be used for a 10-30 minute LAN experiment without expected application-level crashes.
- [ ] **RELY-04**: Existing unit tests continue to pass after the package restructure.
- [ ] **RELY-05**: Legacy teleoperation tests continue to pass so retained compatibility is protected.

### Documentation

- [ ] **DOC-01**: Project includes an environment setup guide under `docs/`.
- [ ] **DOC-02**: Environment guide covers GPU/server machine setup, including Python, LeRobot, CUDA/PyTorch checks, SmolVLA model path, HuggingFace access, and policy server preflight checks.
- [ ] **DOC-03**: Environment guide covers robot-side setup, including LeRobot, SO-101 serial permissions, follower calibration id, cameras, and robot client preflight checks.
- [ ] **DOC-04**: Environment guide covers LAN communication checks, including server IP/port, firewall, ping/basic connectivity, and time synchronization guidance for trustworthy metrics.
- [ ] **DOC-05**: Environment guide covers dry-run/mock operation.
- [ ] **DOC-06**: Environment guide covers common failures: LeRobot import failure, CUDA unavailable, invalid model path, camera index mismatch, serial port permission failure, server connection failure, and metrics output confusion.

### Configuration

- [ ] **CONF-01**: v1 can keep script-level constants as the primary configuration path.
- [ ] **CONF-02**: Code structure leaves a future path for CLI or YAML overrides without making that a blocker for the first working release.
- [ ] **CONF-03**: Operator-facing constants are documented clearly enough to edit before a real run.

## v2 Requirements

Deferred to future releases. These are in the project roadmap but should not block the first practical v1.

### Teleoperation

- **TELE-01**: Legacy teleoperation can be integrated into the new runtime/metrics framework.
- **TELE-02**: Teleoperation and model inference can be compared under shared metrics.
- **TELE-03**: Teleoperation can optionally support fallback/manual override workflows if needed later.

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
- **NET-01**: Non-LAN deployment guidance is added for VPN or cross-network experiments.

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
| STRC-01 | Phase 1 | Pending |
| STRC-02 | Phase 1 | Pending |
| STRC-03 | Phase 1 | Pending |
| STRC-04 | Phase 1 | Pending |
| RUN-01 | Phase 4 | Pending |
| RUN-02 | Phase 4 | Pending |
| RUN-03 | Phase 4 | Pending |
| RUN-04 | Phase 4 | Pending |
| RUN-05 | Phase 4 | Pending |
| METR-01 | Phase 2 | Pending |
| METR-02 | Phase 2 | Pending |
| METR-03 | Phase 2 | Pending |
| METR-04 | Phase 2 | Pending |
| METR-05 | Phase 2 | Pending |
| METR-06 | Phase 2 | Pending |
| METR-07 | Phase 2 | Pending |
| METR-08 | Phase 2 | Pending |
| METR-09 | Phase 2 | Pending |
| EXP-01 | Phase 2 | Pending |
| EXP-02 | Phase 2 | Pending |
| EXP-03 | Phase 2 | Pending |
| EXP-04 | Phase 2 | Pending |
| EXP-05 | Phase 2 | Pending |
| DRY-01 | Phase 3 | Pending |
| DRY-02 | Phase 3 | Pending |
| DRY-03 | Phase 3 | Pending |
| ADPT-01 | Phase 3 | Pending |
| ADPT-02 | Phase 3 | Pending |
| ADPT-03 | Phase 3 | Pending |
| ADPT-04 | Phase 3 | Pending |
| ADPT-05 | Phase 3 | Pending |
| RELY-01 | Phase 3 | Pending |
| RELY-02 | Phase 3 | Pending |
| RELY-03 | Phase 4 | Pending |
| RELY-04 | Phase 5 | Pending |
| RELY-05 | Phase 5 | Pending |
| DOC-01 | Phase 1 | Pending |
| DOC-02 | Phase 1 | Pending |
| DOC-03 | Phase 1 | Pending |
| DOC-04 | Phase 1 | Pending |
| DOC-05 | Phase 1 | Pending |
| DOC-06 | Phase 1 | Pending |
| CONF-01 | Phase 1 | Pending |
| CONF-02 | Phase 1 | Pending |
| CONF-03 | Phase 1 | Pending |

**Coverage:**
- v1 requirements: 44 total
- Mapped to phases: 44
- Unmapped: 0

---
*Requirements defined: 2026-05-11*
*Last updated: 2026-05-11 after roadmap creation*
