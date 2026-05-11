---
phase: 3
slug: dry-run-adapters-and-reliability-hooks
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-11
research: skipped_by_user
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python standard-library `unittest` |
| **Config file** | none |
| **Quick run command** | `python3 -m unittest tests.test_adapters tests.test_dryrun tests.test_reliability -v` |
| **Full suite command** | `python3 -m unittest discover -s tests -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run the focused test module for the touched subsystem.
- **After every plan wave:** Run `python3 -m unittest discover -s tests -v`.
- **Before `$gsd-verify-work`:** Full suite must be green.
- **Max feedback latency:** 30 seconds.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | ADPT-01, ADPT-02 | T3-01 | Adapter protocols stay import-safe and hardware-free | unit/import | `python3 -m unittest tests.test_adapters -v` | ❌ W1 | ⬜ pending |
| 3-01-02 | 01 | 1 | ADPT-03, ADPT-04, ADPT-05 | T3-02 | Concrete placeholders do not require plugin registry or second backend | unit | `python3 -m unittest tests.test_adapters -v` | ❌ W1 | ⬜ pending |
| 3-02-01 | 02 | 2 | DRY-01, DRY-02, DRY-03 | T3-03 | Dry-run records artifacts without pretending hardware validation | unit/fs | `python3 -m unittest tests.test_dryrun -v` | ❌ W2 | ⬜ pending |
| 3-02-02 | 02 | 2 | DRY-02, RELY-01 | T3-04 | Dry-run emits diagnostic events into same artifact set | unit/fs | `python3 -m unittest tests.test_dryrun -v` | ❌ W2 | ⬜ pending |
| 3-03-01 | 03 | 3 | RELY-01 | T3-05 | Error events include stage, component, and exception context | unit | `python3 -m unittest tests.test_reliability -v` | ❌ W3 | ⬜ pending |
| 3-03-02 | 03 | 3 | RELY-02 | T3-06 | Retry helper is bounded and records retry/recovery/exception events | unit | `python3 -m unittest tests.test_reliability -v` | ❌ W3 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. New tests are created in the same standard-library `unittest` style.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dry-run wording does not overclaim hardware validation | DRY-03 | Human-facing semantics matter | Inspect dry-run terminal/docs strings and confirm they say dry-run validates code path and metrics plumbing only. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
