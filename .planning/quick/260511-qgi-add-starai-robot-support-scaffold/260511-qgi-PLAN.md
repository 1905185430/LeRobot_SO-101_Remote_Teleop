---
quick_id: 260511-qgi
slug: add-starai-robot-support-scaffold
type: quick
status: planned
requirements: []
must_haves:
  truths:
    - "StarAI robot types are accepted in config-driven LeRobot robot factories."
    - "StarAI follower/leader types are accepted in TCP teleoperation runtime."
    - "TCP teleoperation supports StarAI dict-shaped action keys without forcing SO-101 joint names."
    - "Support stays lazy-imported and testable without LeRobot or StarAI hardware installed."
    - "Docs explain the supported StarAI type aliases and setup boundary."
  artifacts:
    - path: "so101_remote/starai.py"
      provides: "StarAI LeRobot type aliases and lazy builder helpers"
---

# Quick Task: Add StarAI robot support scaffold

## Scope

Add config and runtime support for StarAI arms through LeRobot-backed modules. The implementation should not claim hardware validation; it should make the project able to accept StarAI config types, lazy-load LeRobot StarAI classes, and use generic dict action payloads in TCP teleoperation.

## Tasks

1. Add StarAI LeRobot helper module.
   - Files: `so101_remote/starai.py`
   - Verify: fake modules can build follower and leader objects.

2. Extend LeRobot factory and TCP teleop validation.
   - Files: `so101_remote/lerobot_factory.py`, `so101_remote/teleop_tcp.py`
   - Verify: StarAI config is accepted and SO-101 tests still pass.

3. Add sample configs and docs.
   - Files: `configs/remote_teleop_starai_tcp.yaml`, `docs/PROJECT_CN.md`, `README.md`
   - Verify: dry-run parses StarAI config.

4. Run regression tests.
   - Verify: `python3 -m unittest discover -s tests -v` and `git diff --check`.
