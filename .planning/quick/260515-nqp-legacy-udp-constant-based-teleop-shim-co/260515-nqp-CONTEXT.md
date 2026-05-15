# Quick Task 260515-nqp: Clean Mainline Codebase - Context

**Gathered:** 2026-05-15
**Status:** Ready for execution

<domain>
## Task Boundary

The user wants a clean, latest-mainline codebase. They explicitly do not want compatibility code and do not want to keep legacy paths.

This task removes old compatibility surfaces and keeps the config-driven `lerobot_remote` architecture as the only documented and tested path.

</domain>

<decisions>
## Implementation Decisions

### Remove Compatibility
- Remove root constant-based entrypoints `policy_server.py` and `robot_client.py`.
- Remove tests that exist only for those compatibility entrypoints.
- Keep config-driven remote inference through `scripts/run_server.py` / `scripts/run_client.py`.

### Remove Legacy
- Remove `legacy/` UDP teleoperation code and legacy tests.
- Move any small still-needed helper logic into the main package before deleting legacy.

### Remove Teleop Shim
- Remove `lerobot_remote/runtime/remote_teleop.py`.
- Use `lerobot_remote/runtime/teleoperation.py` as the sole teleoperation runtime module.

### Clean Working Tree
- Restore the local uncommitted safety config change in `configs/teleop/local_starai_tcp.yaml`.
- Add ignores for local run artifacts and editor/tool state so the code tree stays clean.

</decisions>

<specifics>
## Specific Ideas

- `lerobot_remote/teleop/actions.py` currently imports from `legacy.protocol`; inline the SO-101 action constants and normalization there.
- Update README, architecture, setup, validation, and project docs to remove legacy/compatibility language.
- Delete `docs/compatibility/LEGACY_ENTRYPOINTS_CN.md` because compatibility is no longer a project goal.

</specifics>

<canonical_refs>
## Canonical References

- `docs/ARCHITECTURE_CN.md`
- `README.md`
- `lerobot_remote/teleop/actions.py`
- `lerobot_remote/runtime/teleoperation.py`
- `tests/`

</canonical_refs>
