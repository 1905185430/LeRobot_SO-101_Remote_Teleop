---
quick_id: 260511-qgi
slug: add-starai-robot-support-scaffold
type: quick
status: complete
completed_at: 2026-05-11
---

# Quick Task Summary: Add StarAI robot support scaffold

## Completed

- Added `so101_remote.starai` with LeRobot-backed StarAI follower/leader type aliases and lazy builder helpers.
- Added support for StarAI follower types in `so101_remote.lerobot_factory`.
- Extended TCP teleoperation runtime to accept StarAI follower and leader types.
- Updated teleop action normalization so dict-shaped StarAI actions can keep their native joint keys instead of being forced into SO-101 joint names.
- Added `configs/remote_teleop_starai_tcp.yaml` as a StarAI Viola follower / Violin leader TCP teleop example.
- Added fake-LeRobot StarAI tests covering type support, builders, LeRobot factory construction, and generic dict action normalization.
- Updated English and Chinese docs with StarAI setup notes and commands.

## Verification

- `python3 -m unittest tests.test_starai -v`
- `python3 scripts/run_server.py --config configs/remote_teleop_starai_tcp.yaml --dry-run`
- `python3 scripts/run_client.py --config configs/remote_teleop_starai_tcp.yaml --dry-run`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`
