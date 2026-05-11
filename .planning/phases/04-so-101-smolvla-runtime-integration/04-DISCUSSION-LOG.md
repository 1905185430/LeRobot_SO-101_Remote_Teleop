# Phase 4: SO-101 SmolVLA Runtime Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-11T04:00:13Z
**Phase:** 4-SO-101 SmolVLA Runtime Integration
**Areas discussed:** Runtime boundaries, Run artifacts, Failure handling, Operator constants and logs

---

## Runtime Boundaries

| Option | Description | Selected |
|--------|-------------|----------|
| Conservative move | Mostly move existing script logic into `so101_remote.server/client` while preserving current shape. | |
| Lightweight orchestration | Add small helpers around config construction, metadata, recorder setup, reliability events, and startup. | ✓ |
| Runtime objects | Introduce fuller server/client runtime classes to manage lifecycle. | |

**User's choice:** Lightweight orchestration.
**Notes:** User selected "轻量编排". This should stay pragmatic and avoid a platform rewrite.

---

## Run Artifacts

| Option | Description | Selected |
|--------|-------------|----------|
| Robot client only | Only the robot-side client creates experiment artifacts for v1. | |
| Server/client separate | Server and robot client each create their own run directory. | ✓ |
| Shared run id | Coordinate both machines under a shared run identifier. | |

**User's choice:** Server/client each own a run directory.
**Notes:** Each side should save enough overlapping metadata for manual correlation. Shared run IDs are not required in this phase.

---

## Failure Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Startup only | Record LeRobot import/config/model/camera/serial startup failures. | |
| Connection only | Record network/client connection and action receive failures. | |
| Startup and connection | Record both classes of failure, while re-raising exceptions. | ✓ |

**User's choice:** Startup and connection recording, but do not swallow exceptions.
**Notes:** Retry is acceptable only for bounded safe connection/setup cases, not robot action execution.

---

## Operator Constants And Logs

| Option | Description | Selected |
|--------|-------------|----------|
| Constants only | Keep current constants with no resolved settings helper. | |
| Print settings | Print resolved settings before startup. | |
| Print and save settings | Keep constants, print resolved settings, and save them into metadata. | ✓ |
| YAML/CLI config | Add a broader configuration layer. | |

**User's choice:** Keep constants, print and save resolved settings.
**Notes:** Do not add YAML or broad CLI override support in Phase 4.

---

## the agent's Discretion

- Exact helper names and file placement can be decided during planning.
- Planner/researcher should inspect LeRobot startup flow to decide which operations are safe for bounded retry.

## Deferred Ideas

- Shared cross-machine run IDs and merged server/client reports.
- YAML configuration and CLI override system.
- Retrying robot action execution or hiding control-loop failures.
