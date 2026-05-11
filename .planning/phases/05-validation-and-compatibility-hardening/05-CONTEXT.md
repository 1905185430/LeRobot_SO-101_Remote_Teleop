# Phase 5: Validation And Compatibility Hardening - Context

**Gathered:** 2026-05-11T09:43:45Z
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 5 closes v1 by proving the restructured project remains testable and compatible, documenting what each validation layer can and cannot prove, and preserving future v2 directions without implementing them now. This phase should harden confidence in the current SO-101 + SmolVLA remote inference path, protect the retained legacy UDP teleoperation tests, and write clear validation notes for unit-only, dry-run-only, real LeRobot, hardware, and LAN experiment checks.

It must not add multi-arm runtime support, wireless teleoperation integration, new VLA policy backends, YAML/CLI configuration, reporting dashboards, or non-LAN deployment. Those belong in the documented v2 continuation path.

</domain>

<decisions>
## Implementation Decisions

### Validation Matrix
- **D-01:** Use a strict layered validation matrix. Phase 5 documentation should separate `unit-only`, `dry-run-only`, `real LeRobot required`, `hardware-required`, and `10-30 min LAN required` checks.
- **D-02:** Phase 5 should explicitly preserve pending human validation where hardware or real LAN behavior is required. Automated tests must not imply proof of SO-101 hardware, camera frames, model loading, or physical control-loop stability.

### Legacy Teleoperation Compatibility
- **D-03:** Treat legacy UDP teleoperation as retained compatibility/reference code, not the v1 main runtime path.
- **D-04:** Phase 5 should protect legacy behavior by keeping top-level discovery tests passing and documenting the legacy path's status. It should not integrate legacy UDP teleoperation into the new runtime or artifact system in this phase.

### v2 Continuation Path
- **D-05:** Document v2 continuation items as separate roadmap-style directions, not as one broad bucket. At minimum, separate multi-arm support, wireless teleoperation integration, VLA/PI policy expansion, YAML/CLI configuration, non-LAN deployment, and reporting/plots.
- **D-06:** Fold the pending todo `Plan multi-arm wireless teleoperation and VLA inference` into Phase 5 as documentation/planning context only. The todo informs the v2 continuation path; it does not authorize implementation in Phase 5.

### Allowed Fixes
- **D-07:** Phase 5 may make small fixes when tests, documentation checks, or legacy compatibility expose issues.
- **D-08:** Allowed fixes are limited to tests, documentation, compatibility glue, or clear bug fixes required to make the existing scope truthful. Phase 5 must not add new runtime capabilities.

### v1 Completion Standard
- **D-09:** Phase 5 completion can mark v1 code, documentation, and automated verification as complete while leaving real 10-30 minute LAN/hardware UAT tracked as pending human validation.
- **D-10:** The final milestone status should be honest: automated readiness is complete, but hardware validation remains a separate human-run experiment unless the user performs it.

### the agent's Discretion
- The planner may choose the exact validation document location and structure, provided it clearly separates automated checks from hardware-required checks.
- The planner may decide whether small fixes belong in test files, documentation, or compatibility glue, as long as no new runtime capability is introduced.

### Folded Todos
- `Plan multi-arm wireless teleoperation and VLA inference` — Folded into Phase 5 only as v2 continuation context. It should shape the future-roadmap section by explicitly naming multi-arm support, wireless teleoperation, and VLA inference expansion as future work.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Scope And Requirements
- `.planning/ROADMAP.md` — Phase 5 goal, success criteria, and planned slices.
- `.planning/REQUIREMENTS.md` — RELY-04 and RELY-05 traceability plus v2 requirements and deferred items.
- `.planning/PROJECT.md` — project constraints, validated requirements, legacy teleoperation positioning, and v2 boundaries.
- `.planning/STATE.md` — current phase status, pending human validation concerns, and folded todo reference.
- `.planning/todos/pending/2026-05-11-plan-multi-arm-wireless-teleoperation-and-vla-inference.md` — folded todo informing the v2 continuation path.

### Runtime And Test Code
- `policy_server.py` — thin policy server entrypoint that should remain compatible.
- `robot_client.py` — thin robot client entrypoint and exported operator constants/helpers.
- `so101_remote/server.py` — real policy server orchestration and artifact/reliability path from Phase 4.
- `so101_remote/client.py` — real robot client orchestration and artifact/reliability path from Phase 4.
- `so101_remote/config.py` — v1 constants and local operator settings.
- `so101_remote/recorder.py` — run artifact and summary helpers.
- `so101_remote/metrics.py` — metric sample/event models and terminal summary helper.
- `so101_remote/dryrun.py` — dry-run artifact and reliability plumbing.

### Legacy Compatibility
- `legacy/protocol.py` — custom UDP message contract retained for legacy tests.
- `legacy/leader_sender.py` — leader-side UDP teleoperation sender.
- `legacy/follower_receiver.py` — follower-side UDP teleoperation receiver.
- `legacy/logging_utils.py` — legacy logging setup.
- `tests/test_legacy_demo.py` — top-level bridge that keeps legacy tests discoverable.
- `legacy/tests/test_protocol.py` — legacy protocol coverage.
- `legacy/tests/test_runtime.py` — legacy runtime/UDP behavior coverage.

### Validation And Documentation
- `tests/test_minimal_async_scripts.py` — fake-LeRobot coverage for thin entrypoints and runtime artifacts.
- `tests/test_recorder.py` — run artifact and summary coverage.
- `tests/test_reliability.py` — reliability event/retry/exception helper coverage.
- `tests/test_dryrun.py` — dry-run artifact coverage.
- `docs/ENVIRONMENT.md` — environment setup, artifact checks, and 10-30 minute LAN readiness guidance.
- `README.md` — operator-facing workflow and runtime artifact guidance.
- `.planning/phases/04-so-101-smolvla-runtime-integration/04-VERIFICATION.md` — Phase 4 verification report showing automated PASS and pending hardware UAT boundary.
- `.planning/phases/04-so-101-smolvla-runtime-integration/04-HUMAN-UAT.md` — pending human LAN/hardware validation item.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `python3 -m unittest discover -s tests -v` is the repository-level verification command and currently covers main runtime, metrics, dry-run, reliability, and legacy behavior.
- Existing fake LeRobot module tests allow runtime wrapper validation without LeRobot installed.
- Existing legacy tests cover UDP protocol shape, sequence numbers, timeout/hold behavior, latency logging, invalid packet counting, and RTT tracking.
- Phase 4 artifacts already include `04-VERIFICATION.md` and `04-HUMAN-UAT.md`, which can anchor validation-status documentation.

### Established Patterns
- Tests use standard-library `unittest`; no pytest or CI framework is present.
- Hardware and LeRobot interactions are mocked/stubbed in automated tests.
- Documentation should be explicit about validation boundaries rather than implying real hardware proof.
- The project preserves legacy compatibility while keeping LeRobot async inference as the v1 main path.

### Integration Points
- Phase 5 plans should likely touch tests, README/docs, `.planning` verification artifacts, and possibly small compatibility glue if tests reveal drift.
- Phase 5 should update requirements/project/roadmap evidence if RELY-04 and RELY-05 become validated.
- Any final status should reference the pending human UAT item rather than closing it prematurely.

</code_context>

<specifics>
## Specific Ideas

- Preferred validation wording: automated readiness can be complete while real hardware/LAN validation remains pending.
- Preferred legacy wording: legacy UDP teleoperation is retained compatibility/reference code, not the v1 main runtime path.
- Preferred v2 structure: split future work into separate items for multi-arm support, wireless teleoperation integration, VLA/PI policy expansion, YAML/CLI configuration, non-LAN deployment, and reporting/plots.
- Small fixes are allowed only to keep existing scope truthful and passing.

</specifics>

<deferred>
## Deferred Ideas

- Implementing multiple robot arms is deferred.
- Integrating wireless teleoperation into the new runtime/metrics artifact system is deferred.
- Adding new VLA/PI policy backends is deferred.
- YAML/CLI configuration, non-LAN deployment, and reporting/plotting remain deferred v2-style work.

</deferred>

---

*Phase: 5-Validation And Compatibility Hardening*
*Context gathered: 2026-05-11T09:43:45Z*
