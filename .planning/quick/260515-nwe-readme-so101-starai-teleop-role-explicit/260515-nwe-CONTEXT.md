# Quick Task 260515-nwe: Documentation Trim - Context

**Gathered:** 2026-05-15
**Status:** Ready for execution

<domain>
## Task Boundary

Trim the documentation system so it no longer repeats the same commands and architecture explanations across multiple files. Remove obsolete commands and stale compatibility references after the clean-mainline refactor.

</domain>

<decisions>
## Implementation Decisions

### Documentation Ownership
- `README.md`: short project entrypoint and document map only.
- `docs/ARCHITECTURE_CN.md`: canonical code/path mental model.
- `docs/setup/ENVIRONMENT.md`: environment and hardware/network preflight.
- `docs/reproduction/REPRODUCTION.md`: reproduction index, not a full duplicate guide.
- Specific reproduction docs keep detailed run history and troubleshooting.
- `docs/validation/VALIDATION.md`: validation boundaries only.

### Redundancy Cleanup
- Remove `docs/project/PROJECT_CN.md` because it duplicates README, architecture, setup, and reproduction content.
- Update `docs/README.md` after deleting the project doc.
- Replace outdated generic teleop commands with `run_teleop_follower.py` / `run_teleop_leader.py`.

</decisions>

<specifics>
## Specific Ideas

- Keep README under roughly 80 lines.
- Convert `docs/reproduction/REPRODUCTION.md` into a concise index with test commands.
- Update `SO101_WIRELESS_TCP_TELEOP.md` to role-explicit teleop commands.

</specifics>

<canonical_refs>
## Canonical References

- `README.md`
- `docs/ARCHITECTURE_CN.md`
- `docs/reproduction/STARAI_LOCAL_TCP_TELEOP.md`
- `docs/reproduction/SO101_WIRELESS_TCP_TELEOP.md`
- `docs/setup/ENVIRONMENT.md`
- `docs/validation/VALIDATION.md`

</canonical_refs>
