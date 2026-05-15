# Quick Task 260515-mrg: Architecture Understandability Refactor - Plan

**Mode:** quick
**Created:** 2026-05-15
**Status:** Ready

## Goal

Make the current architecture easier for the project owner to understand and adjust by reducing role ambiguity, documenting the active call paths, and marking old paths as transitional without breaking validated commands.

## Task 1: Add role-explicit TCP teleop entrypoints

**Files**
- `scripts/run_teleop_follower.py`
- `scripts/run_teleop_leader.py`
- `README.md`

**Action**
- Add thin wrappers for TCP teleoperation roles:
  - follower wrapper validates `remote_teleoperation` config, prints summary, then calls `run_tcp_teleop_follower_server`.
  - leader wrapper validates `remote_teleoperation` config, prints summary, then calls `run_tcp_teleop_leader_client`.
- Keep `scripts/run_server.py` and `scripts/run_client.py` unchanged as general config-driven entrypoints.
- Document the new role-explicit commands as preferred for teleoperation.

**Verify**
- `python3 scripts/run_teleop_follower.py --config configs/teleop/local_starai_tcp.yaml --dry-run`
- `python3 scripts/run_teleop_leader.py --config configs/teleop/local_starai_tcp.yaml --dry-run`

**Done**
- Teleop users no longer need to remember that "server" means follower and "client" means leader.

## Task 2: Refactor teleop runtime naming with compatibility shim

**Files**
- `lerobot_remote/runtime/teleoperation.py`
- `lerobot_remote/runtime/remote_teleop.py`
- `lerobot_remote/runtime/__init__.py`
- `lerobot_remote/runtime/dispatch.py`

**Action**
- Move the real TCP teleoperation orchestration functions into a role-explicit module.
- Keep `remote_teleop.py` as a small compatibility re-export so existing imports continue to work.
- Update runtime imports to use the clearer module.

**Verify**
- Existing teleop tests still pass.
- Existing `run_server.py` and `run_client.py` dry-runs still work.

**Done**
- The runtime package has a clearer place for teleoperation orchestration while preserving compatibility.

## Task 3: Add architecture guide and legacy transition notes

**Files**
- `docs/ARCHITECTURE_CN.md`
- `docs/compatibility/LEGACY_ENTRYPOINTS_CN.md`
- `README.md`

**Action**
- Add a Chinese guide with:
  - recommended paths,
  - StarAI TCP teleop flow,
  - remote inference flow,
  - package responsibility map,
  - where to change common behavior.
- Add a compatibility note explaining `policy_server.py`, `robot_client.py`, and `legacy/` as transitional paths.
- Update README top section to point confused readers to the architecture guide first.

**Verify**
- Documentation links resolve.
- README clearly separates recommended, compatibility, and legacy paths.

**Done**
- A new reader can identify the active path and the old paths without reading source first.

## Overall Verification

- `python3 -m unittest tests.test_tcp_teleop tests.test_configured_runtime tests.test_starai -v`
- Dry-run both new role-explicit entrypoints.
- Dry-run existing generic server/client entrypoints for the same config.
