# Quick Summary: Organize Docs Into Topic Folders

Date: 2026-05-11
Status: Complete

## Changes

- Added `docs/README.md`.
- Moved docs into:
  - `docs/setup/ENVIRONMENT.md`
  - `docs/project/PROJECT_CN.md`
  - `docs/validation/VALIDATION.md`
  - `docs/reproduction/REPRODUCTION.md`
  - `docs/reproduction/STARAI_LOCAL_TCP_TELEOP.md`
  - `docs/reproduction/SO101_WIRELESS_TCP_TELEOP.md`
- Updated root `README.md` links and internal doc references.

## Verification

- Passed: old root doc path search returned no stale references.
- Passed: `git diff --check`
- Passed: `python3 -m unittest tests.test_config_loader -v`
