# Quick Task 260515-nwe: Documentation Trim - Plan

**Mode:** quick
**Created:** 2026-05-15
**Status:** Ready

## Goal

Make project documentation smaller and less contradictory by assigning each document one purpose, deleting duplicated project overview content, and updating old teleoperation commands to role-explicit entrypoints.

## Task 1: Collapse top-level docs

**Files**
- `README.md`
- `docs/README.md`
- `docs/project/PROJECT_CN.md`

**Action**
- Rewrite README as a short project landing page with core commands and links.
- Remove `docs/project/PROJECT_CN.md`.
- Update `docs/README.md` to point to the remaining canonical docs.

**Verify**
- README links resolve.
- No references remain to deleted `docs/project/PROJECT_CN.md`.

## Task 2: De-duplicate reproduction docs

**Files**
- `docs/reproduction/REPRODUCTION.md`
- `docs/reproduction/SO101_WIRELESS_TCP_TELEOP.md`
- `docs/reproduction/STARAI_LOCAL_TCP_TELEOP.md`

**Action**
- Convert `REPRODUCTION.md` into a concise index and validation command list.
- Update SO-101 wireless teleop commands to `run_teleop_follower.py` and `run_teleop_leader.py`.
- Keep StarAI local teleop as the detailed successful local reproduction doc.

**Verify**
- `rg "scripts/run_server.py --config configs/teleop|scripts/run_client.py --config configs/teleop" docs README.md` returns no stale teleop commands.

## Task 3: Remove stale architecture tail and validate

**Files**
- `docs/ARCHITECTURE_CN.md`
- `docs/setup/ENVIRONMENT.md`
- `docs/validation/VALIDATION.md`

**Action**
- Remove stale removed-path section from architecture guide.
- Keep setup and validation focused; do not duplicate runbooks.

**Verify**
- `python3 -m unittest discover -s tests -v`
- `git diff --check`
