# Roadmap: SO-101 Remote VLA Inference Experiments

## Overview

The roadmap turns the current two-script playground into a lightweight remote VLA inference experiment framework. It starts by creating a small package structure and environment guide, then adds communication metrics and run artifacts, validates the runtime through dry-run mode, wires the real SO-101 + SmolVLA LeRobot path, and finishes by hardening tests, compatibility, and v2 extension boundaries.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Package And Environment Baseline** - Establish the lightweight package, thin entrypoints, constants documentation, and environment setup guide. (completed 2026-05-11)
- [x] **Phase 2: Metrics And Run Artifacts** - Build communication metric collection, structured storage, run directories, and lightweight summaries. (completed 2026-05-11)
- [x] **Phase 3: Dry Run, Adapters, And Reliability Hooks** - Add mock execution, minimal adapter boundaries, and practical error/recovery recording. (completed 2026-05-11)
- [x] **Phase 4: SO-101 SmolVLA Runtime Integration** - Wire the real LeRobot async inference server/client path through the new structure. (completed 2026-05-11)
- [x] **Phase 5: Validation And Compatibility Hardening** - Verify long-run readiness, tests, legacy compatibility, and future extension boundaries. (completed 2026-05-11)

## Phase Details

### Phase 1: Package And Environment Baseline
**Goal**: Establish the lightweight project shape and setup documentation without changing the intended runtime behavior.
**Depends on**: Nothing (first phase)
**Requirements**: STRC-01, STRC-02, STRC-03, STRC-04, DOC-01, DOC-02, DOC-03, DOC-04, DOC-05, DOC-06, CONF-01, CONF-02, CONF-03
**Success Criteria** (what must be TRUE):
  1. Developer can import `so101_remote` and find runtime, metrics, recorder, adapter, and dry-run module locations.
  2. Operator can still start through `policy_server.py` and `robot_client.py`.
  3. Existing legacy code remains isolated under `legacy/`.
  4. `docs/ENVIRONMENT.md` explains server, robot-side, LAN, dry-run, and common failure setup.
  5. Operator-facing constants are documented clearly enough for a real LAN experiment.
**Plans**: 3 plans

Plans:
**Wave 1**
- [x] 01-01: Create `so101_remote/` package skeleton and thin entrypoint handoff.
- [x] 01-03: Write environment setup guide and constant-editing documentation.

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 01-02: Preserve legacy package boundaries and update tests/imports after restructure.

### Phase 2: Metrics And Run Artifacts
**Goal**: Make communication measurements first-class outputs with terminal summaries, structured files, run metadata, and basic Markdown summaries.
**Depends on**: Phase 1
**Requirements**: METR-01, METR-02, METR-03, METR-04, METR-05, METR-06, METR-07, METR-08, METR-09, EXP-01, EXP-02, EXP-03, EXP-04, EXP-05
**Success Criteria** (what must be TRUE):
  1. Runtime code can record latency, RTT-like timing, jitter, loop interval, chunk interval, queue state, and event metrics when signals are available.
  2. Operator can see readable metrics summaries during a run.
  3. Each run creates a unique local directory with metadata and structured metrics files.
  4. Each run can generate a lightweight Markdown summary with count, min, max, mean, and p95 where data exists.
  5. Timeout, disconnect, retry, recovery, and exception events are stored in the same experiment artifact set.
**Plans**: 3 plans

Plans:
- [x] 02-01: Implement metric sample/event models and statistics helpers.
- [x] 02-02: Implement run directory, metadata, JSONL/CSV recorder, and terminal summary output.
- [x] 02-03: Implement lightweight Markdown run summary generation.

### Phase 3: Dry Run, Adapters, And Reliability Hooks
**Goal**: Validate the new runtime and metric plumbing without hardware while keeping future robot/model support lightweight.
**Depends on**: Phase 2
**Requirements**: DRY-01, DRY-02, DRY-03, ADPT-01, ADPT-02, ADPT-03, ADPT-04, ADPT-05, RELY-01, RELY-02
**Success Criteria** (what must be TRUE):
  1. Developer can run dry-run mode on one machine and produce realistic run artifacts.
  2. Dry-run mode validates runtime and metrics plumbing without claiming hardware or model validation.
  3. SO-101 and SmolVLA have concrete lightweight adapter locations.
  4. PI-series policies and other robot arms have clear extension points without a plugin registry.
  5. Startup, connection, timeout, retry, recovery, and exception events are recorded with diagnostic context.
**Plans**: 3 plans

Plans:
- [x] 03-01: Define minimal robot and policy adapter protocols plus SO-101/SmolVLA implementations.
- [x] 03-02: Add dry-run fake robot/policy path that exercises metrics and run artifacts.
- [x] 03-03: Add practical reliability hooks for errors, retries, recovery events, and diagnostics.

### Phase 4: SO-101 SmolVLA Runtime Integration
**Goal**: Route the real LeRobot async inference server and client through the new package while preserving the official transport path.
**Depends on**: Phase 3
**Requirements**: RUN-01, RUN-02, RUN-03, RUN-04, RUN-05, RELY-03
**Success Criteria** (what must be TRUE):
  1. Operator can start the SmolVLA policy server on the GPU/server machine through the thin entrypoint.
  2. Operator can start the SO-101 robot client on the robot-side computer through the thin entrypoint.
  3. Robot client still exposes all necessary SO-101, camera, model, action chunking, aggregation, and queue settings.
  4. Runtime keeps LeRobot official async inference as the transport path.
  5. Startup logs and run metadata identify server, robot, model, endpoint, run directory, and git commit where available.
**Plans**: 3 plans

Plans:
- [x] 04-01: Move server runtime construction into `so101_remote` while keeping `policy_server.py` thin.
- [x] 04-02: Move robot client runtime construction into `so101_remote` while keeping `robot_client.py` thin.
- [x] 04-03: Connect real runtime startup, run metadata, metrics hooks, and 10-30 minute LAN experiment readiness checks.

### Phase 5: Validation And Compatibility Hardening
**Goal**: Prove the restructured project still works, legacy compatibility is protected, and future roadmap items are visible but not overbuilt.
**Depends on**: Phase 4
**Requirements**: RELY-04, RELY-05
**Success Criteria** (what must be TRUE):
  1. Existing minimal async script tests pass after the restructure.
  2. Legacy UDP teleoperation tests pass from top-level discovery.
  3. Validation notes explain which checks are unit-only, dry-run-only, and hardware-required.
  4. v2 items for teleoperation integration, reporting, YAML/CLI config, PI adapter, other robot arms, and non-LAN deployment remain documented without blocking v1.
**Plans**: 2 plans

Plans:
- [x] 05-01: Update and run unit tests for thin entrypoints, package modules, metrics, dry-run, and legacy compatibility.
- [x] 05-02: Document validation status, residual hardware risks, and v2 continuation path.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Package And Environment Baseline | 3/3 | Complete   | 2026-05-11 |
| 2. Metrics And Run Artifacts | 3/3 | Complete   | 2026-05-11 |
| 3. Dry Run, Adapters, And Reliability Hooks | 3/3 | Complete   | 2026-05-11 |
| 4. SO-101 SmolVLA Runtime Integration | 3/3 | Complete   | 2026-05-11 |
| 5. Validation And Compatibility Hardening | 2/2 | Complete | 2026-05-11 |
