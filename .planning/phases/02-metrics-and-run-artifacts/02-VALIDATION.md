---
phase: 2
slug: metrics-and-run-artifacts
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-11
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python standard-library `unittest` |
| **Config file** | none |
| **Quick run command** | `python3 -m unittest tests.test_metrics tests.test_recorder -v` |
| **Full suite command** | `python3 -m unittest discover -s tests -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m unittest tests.test_metrics tests.test_recorder -v` when metrics or recorder code changed.
- **After every plan wave:** Run `python3 -m unittest discover -s tests -v`.
- **Before `$gsd-verify-work`:** Full suite must be green.
- **Max feedback latency:** 30 seconds.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 1 | METR-01..METR-07 | T2-01 | Metrics accept only explicit numeric sample values and typed event data | unit | `python3 -m unittest tests.test_metrics -v` | ❌ W1 | ⬜ pending |
| 2-01-02 | 01 | 1 | METR-03, METR-08 | T2-02 | Statistics and terminal summaries are deterministic | unit | `python3 -m unittest tests.test_metrics -v` | ❌ W1 | ⬜ pending |
| 2-02-01 | 02 | 2 | METR-09, EXP-01..EXP-04 | T2-03 | Run artifacts are written under caller-selected local directories | unit/fs | `python3 -m unittest tests.test_recorder -v` | ❌ W2 | ⬜ pending |
| 2-02-02 | 02 | 2 | EXP-02, EXP-03 | T2-04 | Run metadata records reproducibility fields without requiring secrets | unit/fs | `python3 -m unittest tests.test_recorder -v` | ❌ W2 | ⬜ pending |
| 2-03-01 | 03 | 3 | EXP-05 | T2-05 | Summary generation uses structured artifacts and does not require hardware | unit/fs | `python3 -m unittest tests.test_recorder -v` | ❌ W3 | ⬜ pending |
| 2-03-02 | 03 | 3 | METR-04, EXP-04 | T2-06 | Events appear in the same artifact set as numeric metrics | unit/fs | `python3 -m unittest tests.test_recorder -v` | ❌ W3 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. New tests are created in the same standard-library `unittest` style.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Operator readability of terminal and Markdown summaries | METR-08, EXP-05 | Readability is partly human-facing | Inspect one generated terminal summary string and one `summary.md`; verify metric names, count, min, max, mean, p95, units, and event counts are understandable. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
