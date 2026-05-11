---
quick_id: 260511-qrr
slug: fix-starai-lerobot-module-discovery
type: quick
status: planned
requirements: []
must_haves:
  truths:
    - "StarAI loader uses the actual official package module names installed in the lerobot environment."
    - "StarAI config construction works without connecting hardware."
    - "Existing tests still pass."
  artifacts:
    - path: "so101_remote/starai.py"
      provides: "Correct StarAI module and class discovery"
---

# Quick Task: Fix StarAI LeRobot module discovery

## Scope

Fix StarAI lazy imports to match the actual installed packages in the user's `lerobot` conda environment: `lerobot_robot_viola`, `lerobot_robot_cello`, and `lerobot_teleoperator_violin`.
