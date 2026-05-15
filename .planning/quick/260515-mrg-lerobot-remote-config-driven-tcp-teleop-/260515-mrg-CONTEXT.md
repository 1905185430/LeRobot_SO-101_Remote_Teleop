# Quick Task 260515-mrg: Architecture Understandability Refactor - Context

**Gathered:** 2026-05-15
**Status:** Ready for planning

<domain>
## Task Boundary

Optimize the project structure so the current `lerobot_remote` config-driven TCP teleoperation and remote inference architecture is easier to understand and adjust. The user is currently disoriented because the project was largely created through AI-assisted implementation: it runs, but the code structure is not yet readable to the project owner.

This task should improve the mental model and source layout without breaking the already validated StarAI/SO101 TCP teleoperation commands.

</domain>

<decisions>
## Implementation Decisions

### Scope
- User selected actual module refactoring, not documentation-only cleanup.
- Keep the first refactor small and reversible: prefer role-explicit modules and compatibility shims over broad package moves.
- Avoid large behavior changes in hardware-facing loops.

### Historical Paths
- User selected preparing old paths for removal.
- Do not delete `policy_server.py`, `robot_client.py`, or `legacy/` in this quick task because compatibility tests and historical reproduction notes still depend on them.
- Make old paths visibly transitional/deprecated in documentation so they stop competing with the config-driven path in the user's mental model.

### Audience
- User selected both experiment operator and developer maintainer.
- Architecture documentation should contain a fast operator path and a maintainer path.
- The TCP teleoperation explanation should preserve the user's learned model:
  `YAML config -> run_server initializes follower from robot config -> run_client initializes leader from teleop config -> leader.get_action() -> TCP ACTION -> follower safety checks -> follower.send_action(action)`.

### Agent Discretion
- Preserve existing validated commands.
- Add clearer aliases where that reduces confusion.
- Keep tests focused on importability, dispatch, and teleoperation behavior rather than adding hardware-dependent checks.

</decisions>

<specifics>
## Specific Ideas

- Add role-explicit teleoperation entrypoints such as `scripts/run_teleop_follower.py` and `scripts/run_teleop_leader.py`.
- Introduce a role-explicit runtime module for teleoperation orchestration, while keeping `runtime/remote_teleop.py` as a compatibility shim.
- Add a Chinese architecture guide that explains recommended paths, transitional paths, and the StarAI TCP teleop call chain.
- Update README so recommended config-driven commands are visually separated from compatibility and legacy paths.

</specifics>

<canonical_refs>
## Canonical References

- `configs/teleop/local_starai_tcp.yaml` - validated StarAI local TCP teleoperation config.
- `docs/reproduction/STARAI_LOCAL_TCP_TELEOP.md` - successful StarAI local reproduction guide.
- `lerobot_remote/runtime/dispatch.py` - mode and role dispatch.
- `lerobot_remote/runtime/remote_teleop.py` - current TCP teleop runtime orchestration.
- `lerobot_remote/teleop/client.py` and `lerobot_remote/teleop/server.py` - leader/follower TCP loops.
- `lerobot_remote/robots/factory.py` and `lerobot_remote/robots/starai.py` - hardware construction path.

</canonical_refs>
