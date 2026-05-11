# Phase 5: Validation And Compatibility Hardening - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-11T09:43:45Z
**Phase:** 5-validation-and-compatibility-hardening
**Areas discussed:** Validation matrix, legacy UDP teleoperation positioning, v2 continuation path, allowed fixes, v1 completion standard

---

## Pending Todo Fold-In

| Option | Description | Selected |
|--------|-------------|----------|
| Fold into Phase 5 context | Use the todo as v2 continuation path context only; do not implement it in Phase 5. | ✓ |
| Keep as independent todo | Leave Phase 5 untouched and handle the todo later. | |
| Mention and keep pending | Mention in docs while leaving the pending todo as a separate entry. | |

**User's choice:** Fold into Phase 5 context.
**Notes:** The folded todo is `Plan multi-arm wireless teleoperation and VLA inference`. It informs future-roadmap documentation only.

---

## Validation Matrix

| Option | Description | Selected |
|--------|-------------|----------|
| Strict layered matrix | Separate `unit-only`, `dry-run-only`, `real LeRobot required`, `hardware-required`, and `10-30 min LAN required`. | ✓ |
| Simplified automated/manual split | Shorter docs but less diagnostic precision. | |
| Agent decides | Continue the Phase 4 verification style at the agent's discretion. | |

**User's choice:** 1A — strict layered matrix.
**Notes:** Phase 5 should be explicit about what automated tests prove and what remains human/hardware validation.

---

## Legacy UDP Teleoperation Positioning

| Option | Description | Selected |
|--------|-------------|----------|
| Retained but not main path | Protect legacy tests and document it as compatibility/reference code. | ✓ |
| Future wireless teleoperation basis | Explicitly present legacy UDP as the future integration foundation. | |
| Both | Preserve as non-main path now and call it a possible v2 basis. | |

**User's choice:** 2A — retained but not main path.
**Notes:** Phase 5 should not migrate legacy UDP into the new runtime.

---

## v2 Continuation Path

| Option | Description | Selected |
|--------|-------------|----------|
| Single umbrella direction | Keep multi-arm, wireless teleoperation, and VLA inference as one future bucket. | |
| Split into multiple v2 items | Separate multi-arm support, wireless teleoperation, VLA/PI policy expansion, YAML/CLI config, non-LAN deployment, and reporting/plots. | ✓ |
| Umbrella plus sub-items | Add a broad heading with detailed sub-items. | |

**User's choice:** 3B — split into multiple v2 items.
**Notes:** Future work should be easier to promote into separate phases later.

---

## Allowed Fixes

| Option | Description | Selected |
|--------|-------------|----------|
| Allow small fixes | Fix tests, docs, compatibility glue, and small correctness issues found while validating. | ✓ |
| Documentation/verification only | Record problems but do not patch code. | |
| Allow runtime bug fixes | Fix runtime bugs when found, without adding features. | |

**User's choice:** 4A — allow small fixes.
**Notes:** No new runtime capability should be added in Phase 5.

---

## v1 Completion Standard

| Option | Description | Selected |
|--------|-------------|----------|
| Code complete, hardware UAT pending | Mark v1 code/docs/automated validation complete; keep 10-30 minute LAN validation as pending human UAT. | ✓ |
| Hardware UAT required for v1 complete | Block milestone completion until the real LAN/SO-101 run is performed. | |
| Two-level status | Separately mark `v1 code complete` and `v1 hardware validated`. | |

**User's choice:** 5A — code complete, hardware UAT pending.
**Notes:** The final milestone should remain honest about pending hardware validation.

## the agent's Discretion

- Choose exact validation document structure and file locations.
- Choose small test/doc/compatibility fixes required to keep existing scope truthful.

## Deferred Ideas

- Multi-arm runtime implementation.
- Wireless teleoperation integration into the new runtime and metrics artifact system.
- VLA/PI policy backend expansion.
- YAML/CLI configuration, non-LAN deployment, reporting, and plotting.
