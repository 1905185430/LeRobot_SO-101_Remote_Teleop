---
last_mapped: 2026-05-11
last_mapped_commit: 2dd7d89
focus: concerns
---

# Concerns

## Worktree State

- The working tree is dirty.
- Git shows root-level legacy files as deleted and `legacy/` files as untracked.
- `policy_server.py`, `robot_client.py`, `tests/test_legacy_demo.py`, and `tests/test_minimal_async_scripts.py` are untracked.
- `README.md` is modified.
- This likely represents an in-progress migration from custom UDP teleop to minimal LeRobot async inference.

## Dependency Definition

- There is no dependency manifest.
- Operators must infer installation steps from README and official LeRobot docs.
- Tests stub LeRobot, so local unit tests can pass even if the actual runtime environment cannot run the scripts.

## Configuration Risk

- Main-path settings are hard-coded constants in scripts.
- `SERVER_ADDRESS = "192.168.1.10:8080"` is environment-specific.
- `PRETRAINED_NAME_OR_PATH = "HF_USER/FINETUNE_MODEL_NAME"` is a placeholder that must be changed before real use.
- `POLICY_DEVICE = "cuda"` assumes a CUDA runtime.
- Camera names must match policy observation keys, but this is documented rather than validated.

## Network And Safety

- `policy_server.py` binds to `0.0.0.0`, exposing the server on all interfaces.
- There is no local authentication or encryption in the main scripts; security depends on LeRobot and the surrounding network.
- The legacy UDP bridge has no authentication, encryption, replay protection, or sender allowlist.
- Legacy follower behavior holds the last valid action on timeout; this is intentional but may still be risky for physical hardware depending on pose and task.

## Generated Files

- `__pycache__/` directories are present in the repository tree.
- `logs/` contains generated runtime logs.
- `so101_async/` contains only bytecode cache files, suggesting stale generated state from a removed package.
- These files may cause noise unless ignored or cleaned intentionally.

## Compatibility Risk

- `robot_client.py` includes compatibility logic for multiple LeRobot SO-101 follower config module paths.
- `legacy/leader_sender.py` and `legacy/follower_receiver.py` import specific LeRobot SO-101 modules that may vary across versions.
- Without pinned LeRobot versions, upstream API drift can break runtime behavior.

## Test Gaps

- No tests exercise real LeRobot async inference across a server/client boundary.
- No tests run against real SO-101 hardware.
- No tests validate actual model loading or HuggingFace access.
- No test validates camera frames, policy observation keys, or action dimensionality from a real policy.

## Documentation Gaps

- README gives minimal install guidance and delegates to official LeRobot docs.
- There is no troubleshooting section for serial ports, calibration ids, firewall issues, CUDA availability, camera permissions, or model paths.
- Empty `configs/`, `docs/`, and `scripts/` directories imply planned structure but do not document active behavior.

## Immediate Cleanup Candidates

- Decide whether generated logs and bytecode caches should be removed or ignored.
- Add a dependency/runtime note with tested Python and LeRobot versions.
- Clarify whether `legacy/` is archival reference or still supported.
- Add preflight validation for user-edited constants before touching hardware.
- Consider narrowing server bind address or documenting LAN/firewall assumptions.
