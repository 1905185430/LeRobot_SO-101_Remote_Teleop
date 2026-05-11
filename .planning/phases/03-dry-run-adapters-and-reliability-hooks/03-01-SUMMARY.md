---
phase: 03-dry-run-adapters-and-reliability-hooks
plan: "01"
subsystem: adapters
tags: [python, unittest, adapters, protocols]
requires:
  - phase: 02-metrics-and-run-artifacts
    provides: "Import-safe package and test style"
provides:
  - "Robot and policy adapter protocols"
  - "SO-101 and SmolVLA concrete adapter locations"
  - "PI-series and unsupported backend placeholders"
affects: [dry-run, runtime-integration, pi-series-support]
tech-stack:
  added: []
  patterns: [standard-library protocols, explicit placeholders]
key-files:
  created: [tests/test_adapters.py]
  modified: [so101_remote/adapters/robot.py, so101_remote/adapters/policy.py, so101_remote/adapters/lerobot_so101.py, so101_remote/adapters/__init__.py]
key-decisions:
  - "Adapter modules stay import-safe and do not import LeRobot."
  - "Future PI-series support is represented as an explicit placeholder, not a plugin registry."
patterns-established:
  - "Concrete runtime adapters expose `describe()` while real runtime wiring remains Phase 4."
requirements-completed: [ADPT-01, ADPT-02, ADPT-03, ADPT-04, ADPT-05]
duration: 7min
completed: 2026-05-11
---

# Phase 03: Dry Run, Adapters, And Reliability Hooks Summary

**Import-safe adapter protocols with explicit SO-101, SmolVLA, PI-series, and unsupported backend boundaries**

## Performance

- **Duration:** 7 min
- **Started:** 2026-05-11T03:24:41Z
- **Completed:** 2026-05-11T03:31:00Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Expanded robot and policy adapter protocols.
- Added unsupported robot/policy placeholders with explicit `NotImplementedError` messages.
- Added concrete SO-101 and SmolVLA adapter locations with `describe()` metadata.
- Added adapter tests proving imports remain LeRobot-free.

## Task Commits

1. **Tasks 1-3: Adapter protocols, placeholders, concrete adapter locations, and tests** - `635abcb` (feat)

## Files Created/Modified

- `so101_remote/adapters/robot.py` - Robot protocol and unsupported robot placeholder.
- `so101_remote/adapters/policy.py` - Policy protocol, unsupported policy placeholder, PI-series placeholder.
- `so101_remote/adapters/lerobot_so101.py` - SO-101 and SmolVLA adapter locations.
- `so101_remote/adapters/__init__.py` - Adapter exports.
- `tests/test_adapters.py` - Adapter import and behavior tests.

## Decisions Made

- Kept real LeRobot runtime wiring deferred to Phase 4.
- Used explicit classes instead of registry/discovery machinery.

## Deviations from Plan

None - plan executed exactly as written.

**Total deviations:** 0 auto-fixed.
**Impact on plan:** None.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 03-02 can use fake adapters and Phase 2 recorder APIs to produce dry-run artifacts without hardware.

## Self-Check: PASSED

- `python3 -m unittest tests.test_adapters -v` exits 0.
- `python3 -c "import so101_remote.adapters.robot; import so101_remote.adapters.policy; import so101_remote.adapters.lerobot_so101"` exits 0.
- `rg "PISeriesPolicyPlaceholder|UnsupportedRobotAdapter|SO101LeRobotAdapter|SmolVLAPolicyAdapter" so101_remote/adapters` finds all adapter classes.

---
*Phase: 03-dry-run-adapters-and-reliability-hooks*
*Completed: 2026-05-11*
