# Phase 6: Generalize package architecture from so101_remote to lerobot_remote - Context

**Gathered:** 2026-05-12
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers a repository-internal architecture refactor that renames the implementation package from `so101_remote` to `lerobot_remote` and fully splits the package into clearer platform layers. The goal is to align the codebase with the repository's broader purpose: LeRobot-based remote VLA inference and TCP teleoperation across multiple robot backends.

This phase must preserve the existing user-facing CLI commands and validated runtime behavior for SO-101 wireless TCP teleoperation, StarAI local TCP teleoperation, debug mock TCP paths, and current LeRobot async inference entrypoints.

</domain>

<decisions>
## Implementation Decisions

### Package Migration
- **D-01:** Rename the real implementation package from `so101_remote` to `lerobot_remote`.
- **D-02:** Do not keep a `so101_remote` compatibility shim. All repository imports, tests, scripts, and docs should move to `lerobot_remote`.
- **D-03:** Because there is no compatibility shim, downstream planning must include a complete import migration and a search step proving no repository-owned `so101_remote` imports remain, except historical planning text if intentionally left unchanged.

### Refactor Scope
- **D-04:** Phase 6 should do package migration plus full module splitting, not a shallow package rename.
- **D-05:** Keep the public commands stable:
  - `python3 scripts/run_server.py --config ...`
  - `python3 scripts/run_client.py --config ...`
  - `python3 scripts/run_local.py --config ...`
  - `python3 policy_server.py`
  - `python3 robot_client.py`
- **D-06:** Do not add new runtime capabilities in this phase. WebUI expansion, dataset recording, local inference completion, and new robot/policy backends remain outside this refactor unless strictly required to keep existing behavior working.

### Target Package Layout
- **D-07:** Use a complete layered package layout under `lerobot_remote/`:
  - `config/` for config loading and schema objects.
  - `runtime/` for dispatch and mode-specific runners.
  - `teleop/` for TCP teleoperation client/server/settings/actions/safety.
  - `robots/` for SO-101 and StarAI robot/teleoperator construction.
  - `network/` for length-prefixed TCP protocol and mock TCP helpers.
  - `recording/` for metrics and run artifact recording.
  - `policies/` for LeRobot async/policy construction boundaries.
  - `webui/` for dashboard state and Gradio app code.
- **D-08:** `so101_remote/starai.py` should become robot-specific code under `lerobot_remote/robots/starai.py`.
- **D-09:** SO-101 builder logic currently embedded in `teleop_tcp.py` should move under `lerobot_remote/robots/so101.py` or a closely related robot factory module.
- **D-10:** `teleop_tcp.py` should be split into smaller teleoperation modules instead of moved as one large file.
- **D-11:** `runtime.py` should be split into dispatch and mode-specific runtime modules instead of moved as one large file.
- **D-12:** `metrics.py` and `recorder.py` should move under `lerobot_remote/recording/`.
- **D-13:** `config_loader.py` and `config_schema.py` should move under `lerobot_remote/config/`.

### Compatibility And Verification
- **D-14:** Required automated verification is full unit tests plus dry-run checks for SO-101, StarAI, and debug mock configs.
- **D-15:** Minimum test command:
  - `python3 -m unittest discover -s tests -v`
- **D-16:** Minimum dry-run commands:
  - `python3 scripts/run_server.py --config configs/teleop/remote_so101_tcp.yaml --dry-run`
  - `python3 scripts/run_client.py --config configs/teleop/remote_so101_tcp.yaml --dry-run`
  - `python3 scripts/run_server.py --config configs/teleop/local_starai_tcp.yaml --dry-run`
  - `python3 scripts/run_client.py --config configs/teleop/local_starai_tcp.yaml --dry-run`
  - `python3 scripts/run_server.py --config configs/debug/debug_mock_robot.yaml --dry-run`
  - `python3 scripts/run_client.py --config configs/debug/debug_mock_robot.yaml --dry-run`
- **D-17:** Hardware reruns are not required inside Phase 6 execution, but documentation must not claim fresh hardware validation unless it is actually performed.

### Folded Todos
- **Generalize so101_remote package architecture:** Folded as the core scope for this phase. The package name and module layout must stop implying SO-101-only ownership now that StarAI and future robot backends are part of the repository direction.
- **Plan configurable TCP local and web UI platform:** Folded only as boundary context. It informs the need for a cleaner layered architecture, but WebUI expansion, complete local inference, and broader platform features are deferred beyond this phase.

### the agent's Discretion
- The planner may choose exact filenames inside each target subpackage if they preserve the selected layer responsibilities and keep imports readable.
- The planner may decide whether to keep short re-export `__init__.py` files for ergonomics, as long as there is no `so101_remote` compatibility package.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase And Scope
- `.planning/ROADMAP.md` — Defines Phase 6 and its dependency on Phase 5.
- `.planning/PROJECT.md` — Captures project constraints: lightweight LeRobot-based framework, thin CLIs, no heavy plugin registry, structured metrics, and compatibility.
- `.planning/REQUIREMENTS.md` — Defines existing structure, adapter, reliability, and compatibility requirements that this refactor must preserve.
- `.planning/STATE.md` — Records current completed quick tasks, pending todos, and roadmap evolution.

### Folded Todos
- `.planning/todos/pending/2026-05-12-generalize-so101-remote-package-architecture.md` — Primary design seed for this phase.
- `.planning/todos/pending/2026-05-11-plan-configurable-tcp-local-and-web-ui-platform.md` — Broader platform direction that should inform layering but not expand Phase 6 scope.

### Codebase Maps
- `.planning/codebase/STACK.md` — Runtime stack, LeRobot dependency style, and current test command.
- `.planning/codebase/ARCHITECTURE.md` — Existing thin entrypoints, LeRobot async path, and legacy UDP reference architecture.
- `.planning/codebase/CONVENTIONS.md` — Python style, lazy LeRobot imports, unittest conventions, and error-handling patterns.

### Validated Runtime Documentation
- `docs/reproduction/SO101_WIRELESS_TCP_TELEOP.md` — Documents the currently successful SO-101 wireless TCP teleoperation path that must not be broken.
- `docs/reproduction/STARAI_LOCAL_TCP_TELEOP.md` — Documents the currently successful StarAI local TCP teleoperation path that must not be broken.
- `docs/reproduction/REPRODUCTION.md` — Lists current reproduction and validation commands.
- `docs/project/PROJECT_CN.md` — Chinese project explanation that must be updated to use `lerobot_remote` after migration.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/run_server.py`, `scripts/run_client.py`, and `scripts/run_local.py` are already thin CLI wrappers. They should remain user-facing entrypoints and only update imports to the new package.
- `policy_server.py` and `robot_client.py` are existing thin LeRobot async inference entrypoints and should continue to work.
- `so101_remote/network/` already has the length-prefixed TCP protocol and mock TCP helpers. This can move mostly intact to `lerobot_remote/network/`.
- `so101_remote/recorder.py` and `so101_remote/metrics.py` already provide run artifacts and metrics models; they should move into `lerobot_remote/recording/`.
- `so101_remote/starai.py` already contains StarAI-specific LeRobot discovery and construction logic; it belongs under `lerobot_remote/robots/starai.py`.

### Established Patterns
- LeRobot imports are lazy and should stay lazy so tests can run without LeRobot installed.
- Tests use standard-library `unittest` and fake modules in `sys.modules`; keep that pattern.
- Hardware-facing cleanup is best-effort, while startup/runtime exceptions are recorded and re-raised where appropriate.
- Runtime loops use fixed frequencies and explicit timeout/safety handling.
- Current docs distinguish automated validation from real hardware validation; preserve that honesty after refactor.

### Integration Points
- Repository-owned imports currently reference `so101_remote` in scripts, top-level entrypoints, tests, and README/docs. Phase 6 must migrate these to `lerobot_remote`.
- `tests/test_tcp_teleop.py`, `tests/test_starai.py`, `tests/test_lerobot_factory.py`, `tests/test_config_loader.py`, `tests/test_configured_runtime.py`, and related tests cover most import and behavior surfaces that will change.
- `README.md` references `so101_remote.lerobot_factory`, `so101_remote.network`, and `so101_remote.dryrun`; update these references.
- There is currently an uncommitted local change in `so101_remote/config.py`. Execution planning must inspect and preserve it before moving or deleting files.

</code_context>

<specifics>
## Specific Ideas

- The user explicitly chose a clean break: no `so101_remote` compatibility shim.
- The user explicitly chose full module splitting in the same phase as the package rename.
- The user explicitly chose full layered structure over partial splitting.
- The user explicitly chose automated verification with unit tests plus dry-run checks, not mandatory hardware reruns.

</specifics>

<deferred>
## Deferred Ideas

- Expanding WebUI behavior beyond current boundaries belongs in a later phase.
- Completing real `local_inference` behavior belongs in a later phase.
- Dataset recording and LeRobot dataset export belong in a later phase.
- New robot backends beyond the existing SO-101 and StarAI paths belong in later phases.
- Hardware rerun documentation may be updated after the user manually reruns SO-101/StarAI paths, but it is not required for Phase 6 completion.

</deferred>

---

*Phase: 6-Generalize package architecture from so101_remote to lerobot_remote*
*Context gathered: 2026-05-12*
