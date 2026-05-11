---
quick_id: 260511-qrr
slug: fix-starai-lerobot-module-discovery
type: quick
status: complete
completed_at: 2026-05-11
---

# Quick Task Summary: Fix StarAI LeRobot module discovery

## Completed

- Updated StarAI loader to include top-level official modules:
  - `lerobot_robot_viola`
  - `lerobot_robot_cello`
  - `lerobot_teleoperator_violin`
- Added actual class names exported by those packages:
  - `StaraiViola` / `StaraiViolaConfig`
  - `StaraiCello` / `StaraiCelloConfig`
  - `StaraiViolin` / `StaraiViolinConfig`
- Updated fake-module tests to match the official package shape.

## Verification

- `python3 -m unittest tests.test_starai -v`
- `conda run -n lerobot python -c "... _load_starai_follower_api ... _load_starai_leader_api ..."`
- `conda run -n lerobot python -c "... build_starai_follower_config ..."`
- `python3 -m unittest discover -s tests -v`
