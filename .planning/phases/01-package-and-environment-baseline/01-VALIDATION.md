---
phase: 1
slug: package-and-environment-baseline
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-11
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python standard-library `unittest` |
| **Config file** | none |
| **Quick run command** | `python3 -m unittest tests.test_minimal_async_scripts -v` |
| **Full suite command** | `python3 -m unittest discover -s tests -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m unittest tests.test_minimal_async_scripts -v` when code entrypoints or package modules changed.
- **After every plan wave:** Run `python3 -m unittest discover -s tests -v`.
- **Before `$gsd-verify-work`:** Full suite must be green.
- **Max feedback latency:** 30 seconds.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | STRC-01 | T1-01 | Lazy imports preserve dependency isolation | unit/import | `python3 -c "import so101_remote; import so101_remote.server; import so101_remote.client"` | ✅ | ⬜ pending |
| 1-01-02 | 01 | 1 | STRC-02 | T1-02 | Server entrypoint remains explicit and import-safe | unit | `python3 -m unittest tests.test_minimal_async_scripts -v` | ✅ | ⬜ pending |
| 1-01-03 | 01 | 1 | STRC-03 | T1-03 | Client entrypoint remains explicit and import-safe | unit | `python3 -m unittest tests.test_minimal_async_scripts -v` | ✅ | ⬜ pending |
| 1-02-01 | 02 | 2 | STRC-04 | — | Legacy behavior remains isolated and tested | unit | `python3 -m unittest discover -s tests -v` | ✅ | ⬜ pending |
| 1-03-01 | 03 | 1 | DOC-01..DOC-06 | — | Setup guide documents safe preflight checks | file check | `test -f docs/ENVIRONMENT.md` | ❌ W1 | ⬜ pending |
| 1-03-02 | 03 | 1 | CONF-01..CONF-03 | — | Operator-facing constants are documented | grep | `rg "SERVER_ADDRESS|HOST|PORT|ROBOT_ID|PRETRAINED_NAME_OR_PATH" docs README.md` | ❌ W1 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Environment guide usefulness | DOC-01..DOC-06 | Operator setup depends on actual server/robot environment | Read `docs/ENVIRONMENT.md` and verify it covers GPU server, robot-side computer, LAN checks, dry-run, and troubleshooting. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
