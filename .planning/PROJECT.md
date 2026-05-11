# SO-101 Remote VLA Inference Experiments

## What This Is

This project is a lightweight remote VLA inference experiment framework for SO-101 first, with SmolVLA as the first real policy path. It keeps the current LeRobot async inference direction, but reorganizes the code into a small package with thin CLIs, communication metrics, dry-run support, and enough adapter boundaries to later add PI-series policies and other robot arms.

The goal is not to build a highly integrated robotics platform. The goal is to make remote inference run reliably on a GPU server plus robot-side computer over a local network, record communication parameters clearly, and keep the code structure clean enough for the next experiments.

## Core Value

SO-101 + SmolVLA remote inference must run stably while producing trustworthy communication metrics that can be used for wireless communication experiments.

## Requirements

### Validated

- ✓ Minimal LeRobot async inference server entrypoint exists — `policy_server.py` builds and serves a LeRobot `PolicyServerConfig`.
- ✓ Minimal LeRobot async inference robot client entrypoint exists — `robot_client.py` builds SO-101 camera, robot, and async client config.
- ✓ Current main path uses LeRobot official async inference rather than a custom transport — existing.
- ✓ Legacy custom UDP teleoperation path is preserved under `legacy/` — existing.
- ✓ Legacy protocol validates SO-101 six-joint action payloads and ACK payloads — existing.
- ✓ Legacy UDP runtime includes latency, RTT, timeout, ACK, and packet validation logic — existing.
- ✓ Unit tests cover the current minimal async scripts with fake LeRobot modules — existing.
- ✓ Unit tests keep the legacy UDP demo behavior reachable from top-level test discovery — existing.
- ✓ Codebase map exists in `.planning/codebase/` — generated during initialization.
- ✓ Minimal adapter boundaries for robot and policy/model integration exist, with SO-101/SmolVLA as first concrete locations and PI-series/other arms as placeholders — validated in Phase 03.
- ✓ Dry-run/mock mode runs on one machine without SO-101 hardware and produces real run artifacts while stating its validation boundary — validated in Phase 03.
- ✓ Runtime diagnostic helpers record exception, retry, and recovery events with stage/component context — validated in Phase 03.
- ✓ Simple bounded retry/recovery behavior exists without a complex state machine — validated in Phase 03.
- ✓ Real policy server runtime is routed through `so101_remote.server` while preserving LeRobot official `serve(config)` and the thin `policy_server.py` entrypoint — validated in Phase 04.
- ✓ Real SO-101 robot client runtime is routed through `so101_remote.client` while preserving LeRobot official `RobotClient` and the thin `robot_client.py` entrypoint — validated in Phase 04.
- ✓ Server and client startup write per-side run artifacts with metadata, resolved constants, diagnostic events, and summaries under `logs/experiments/` — validated in Phase 04.
- ✓ Runtime startup/control-loop failures are recorded as diagnostic events and re-raised where appropriate — validated in Phase 04.
- ✓ Documentation describes real runtime artifacts and the 10-30 minute LAN validation required for RELY-03 — validated in Phase 04.
- ✓ Existing unit tests continue to pass after the package restructure — validated in Phase 05.
- ✓ Legacy teleoperation tests continue to pass so retained compatibility is protected — validated in Phase 05.
- ✓ Validation documentation separates unit-only, dry-run-only, real LeRobot required, hardware-required, and 10-30 minute LAN required checks — validated in Phase 05.

### Active

- [ ] Reorganize the code into a small `so101_remote/` package while keeping `policy_server.py` and `robot_client.py` as thin entrypoints.
- [ ] Keep v1 lightweight: no plugin registry, no dashboard, no complex experiment platform, and no overbuilt configuration system.
- [ ] Preserve the real SO-101 + SmolVLA path through LeRobot official async inference.
- [ ] Add communication metrics for latency, RTT, jitter, timeout/disconnect events, control frequency, action chunk arrival intervals, and queue state where the LeRobot APIs expose enough signal.
- [ ] Print communication metrics at runtime in a readable terminal format.
- [ ] Save communication metrics locally as JSONL and/or CSV.
- [ ] Store experiment outputs under a local run/log directory such as `runs/` or `logs/experiments/`.
- [ ] Create one run directory per experiment with enough metadata to connect metrics back to settings and code version.
- [ ] Generate a lightweight Markdown experiment summary with basic statistics; charts and dashboards can wait.
- [ ] Record timeout, disconnect, and runtime exception events clearly.
- [ ] Add an environment setup guide under `docs/`, covering GPU server setup, robot-side setup, LAN checks, time synchronization, dry-run, and common failures.
- [ ] Document setup for Python, LeRobot, CUDA/PyTorch checks, SmolVLA model path or HuggingFace access, SO-101 serial permissions, calibration id, cameras, server IP/port, firewall, and connectivity checks.
- [ ] Keep v1 focused on GPU server + robot-side computer on the same LAN.
- [ ] Keep script-level constants acceptable for v1 configuration, with a future path toward CLI/YAML overrides.
- [ ] Put all requested capabilities into the roadmap, but implement v1 in light/heavy layers so the first release remains practical.

### Out of Scope

- Full dashboard or web UI — useful later, but not needed to make v1 run and measure communication.
- Complex plugin registry — future models and robots need clear adapter seams, not a heavy plugin platform.
- Full experiment management platform — v1 only needs local run directories, logs, and a basic summary.
- Complete YAML configuration system as a v1 blocker — constants can remain initially; configuration can evolve after the runtime shape stabilizes.
- Full migration of legacy teleoperation into the new framework during early v1 — preserve compatibility first, integrate later.
- Public internet or VPN deployment as the primary v1 target — start with GPU server and robot-side computer on the same LAN.

## Context

The current repository is a small Python codebase. The main path has two direct scripts: `policy_server.py` for the GPU/server side and `robot_client.py` for the robot-side computer. Both scripts intentionally defer most behavior to LeRobot official async inference APIs.

The legacy path under `legacy/` contains a custom UDP leader/follower teleoperation bridge. It already has useful protocol validation, latency, RTT, ACK, timeout, and packet-loss behavior that can inform the new metrics design, but it is no longer the recommended inference path.

The project direction is to support wireless communication experiments around remote VLA inference. The important output is not only robot movement; it is also reliable measurement of communication behavior during inference runs.

The first real target is SO-101 + SmolVLA. PI-series model support and other robot arms are expected later, so v1 should avoid hard-coding every design decision to SO-101/SmolVLA, while also avoiding a heavyweight platform.

An environment setup guide is part of the project, not optional documentation. Real experiments need repeatable server setup, robot setup, LAN checks, time synchronization guidance, and troubleshooting before communication metrics can be trusted.

## Constraints

- **Runtime**: Python + LeRobot — the project should build around the existing LeRobot async inference path.
- **Topology**: GPU server plus robot-side computer on the same LAN for v1 — this is the first deployment target.
- **Robot**: SO-101 is the first supported hardware — other arms are roadmap items.
- **Policy**: SmolVLA is the first supported VLA policy — PI-series policies are roadmap items.
- **Configuration**: v1 may keep script constants — do not block early progress on a large YAML/CLI config system.
- **Architecture**: small package + thin CLIs — enough structure for testing and reuse, not a platform rewrite.
- **Metrics**: communication measurements must be structured and saved — terminal-only logs are not enough.
- **Safety**: hardware-facing failures must be visible in logs — timeout/disconnect/exception events should not fail silently.
- **Documentation**: environment setup guidance must be available before serious hardware experiments — setup uncertainty invalidates metrics.
- **Compatibility**: legacy teleoperation behavior should remain tested while it is retained.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use LeRobot official async inference as the v1 transport path | Avoid maintaining a custom transport before the real SO-101 + SmolVLA path is stable | Phase 04 preserved `serve(config)` and `RobotClient(config)` as the runtime path |
| Build a small `so101_remote/` package with thin `policy_server.py` and `robot_client.py` entrypoints | Keeps current scripts usable while making metrics, dry-run, and adapters testable | Phase 04 routed both real entrypoints through package modules |
| Keep v1 lightweight and avoid a highly integrated platform | The project needs reliable experiments, not a general robotics framework | — Pending |
| Add minimal robot/policy adapter boundaries | Future PI-series and other robot arms need a place to attach without overbuilding plugin machinery | — Pending |
| Treat communication metrics as a first-class deliverable | The project is for wireless communication experiments, so latency/RTT/jitter and related stats must be recorded | Phase 04 real startup paths now create structured artifact directories with resolved settings and diagnostic events |
| Put all requested capabilities in the roadmap, but layer v1 by priority | Keeps the project comprehensive without making the first implementation too heavy | — Pending |
| Add a dedicated environment setup guide | Real server/robot/network setup must be repeatable before metrics are meaningful | — Pending |
| Preserve legacy teleoperation compatibility first, integrate it into the new framework later | The old path is useful reference code, but remote inference is the v1 main line | — Pending |
| Keep validation claims layered | Automated tests cannot prove real SO-101 hardware, camera frames, SmolVLA loading, physical control-loop stability, or LAN endurance | Phase 05 documents validation layers in `docs/VALIDATION.md` |
| Split v2 continuation items instead of treating them as one broad request | Multi-arm support, wireless teleoperation integration, VLA/PI policy expansion, YAML/CLI configuration, non-LAN deployment, and reporting/plots have different risks and validation needs | Phase 05 records them as future work, not v1 implementation scope |
| Keep dry-run reliability checks deterministic | Retry/recovery artifacts must be testable without hardware or timing flakiness | Phase 03 implemented a one-failure dry-run connection path with no sleep |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-11 after Phase 04 completion*
