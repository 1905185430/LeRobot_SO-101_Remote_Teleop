# Phase 6: Generalize package architecture from so101_remote to lerobot_remote - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-12
**Phase:** 6-Generalize package architecture from so101_remote to lerobot_remote
**Areas discussed:** Folded todos, Package migration strategy, Phase scope boundary, Target module structure, Compatibility and verification

---

## Folded Todos

| Option | Description | Selected |
|--------|-------------|----------|
| Fold both todos | Use package architecture as core and configurable TCP/WebUI platform as boundary context. | ✓ |
| Fold only architecture todo | Keep discussion strictly on package rename and module boundaries. | |
| Fold none | Discuss only from ROADMAP phase title. | |

**User's choice:** Fold both todos.
**Notes:** The configurable TCP/WebUI todo is boundary context only; it should not expand Phase 6 into new WebUI/local inference features.

---

## Package Migration Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Keep compatibility layer | New implementation in `lerobot_remote`, old `so101_remote` forwards imports for one phase. | |
| Full rename | Rename implementation to `lerobot_remote` and update repository imports; old `so101_remote` imports break. | ✓ |
| Keep old package | Keep `so101_remote` and only add internal multi-robot structure. | |

**User's choice:** Full rename.
**Notes:** The user prefers a clean architecture over temporary old import compatibility.

---

## Phase Scope Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Rename only | Only rename `so101_remote` to `lerobot_remote`; no module splitting. | |
| Rename plus small split | Move robot-specific files, but keep `runtime.py` and `teleop_tcp.py` mostly intact. | |
| Rename plus full split | Rename package and fully split broad modules into layered subpackages. | ✓ |

**User's choice:** Rename plus full split.
**Notes:** The plan must be more careful than a shallow rename because multiple runtime paths have already been validated.

---

## Target Module Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Complete layering | Split `config`, `runtime`, `teleop`, `robots`, `network`, `recording`, `policies`, and `webui`. | ✓ |
| Core layering | Split only `runtime`, `teleop`, and `robots`; keep config/metrics/recorder at package root. | |
| Robot and teleop only | Split `robots` and `teleop`; keep `runtime.py` for now. | |

**User's choice:** Complete layering.
**Notes:** The selected target structure matches the repository-level rename to `lerobot-remote-vla-teleop`.

---

## Compatibility And Verification

| Option | Description | Selected |
|--------|-------------|----------|
| Tests plus dry-run | Run full unit tests and dry-run checks for SO-101, StarAI, and debug mock configs. | ✓ |
| Tests plus dry-run plus hardware notes | Add manual hardware rerun record after the user reruns real arms. | |
| Unit tests only | Run only `python3 -m unittest discover -s tests -v`. | |

**User's choice:** Tests plus dry-run.
**Notes:** Hardware reruns are useful but not required inside the architecture refactor phase.

---

## the agent's Discretion

- Exact internal filenames can be chosen during planning if they preserve the selected layer responsibilities.
- Short `__init__.py` re-exports are acceptable for ergonomics.

## Deferred Ideas

- WebUI expansion.
- Real local inference completion.
- Dataset recording and LeRobot dataset export.
- New robot backends beyond SO-101 and StarAI.
- Hardware rerun documentation after manual validation.
