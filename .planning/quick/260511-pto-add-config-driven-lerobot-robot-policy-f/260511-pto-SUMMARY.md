---
quick_id: 260511-pto
slug: add-config-driven-lerobot-robot-policy-f
type: quick
status: complete
completed_at: 2026-05-11
---

# Quick Task Summary: Add config-driven LeRobot robot/policy factories

## Completed

- Added `so101_remote.lerobot_factory` to translate `PlatformConfig` into LeRobot OpenCV camera, SO-101 follower, async robot client, and policy server config objects.
- Kept LeRobot imports lazy so tests and dry-run paths still work without LeRobot installed.
- Added explicit support checks for the first real path: `so101_follower` robot plus `smolvla` policy.
- Added fake-LeRobot unit tests covering supported construction and unsupported robot/policy errors.
- Documented the new factory boundary in `README.md`.

## Scope Boundary

This quick task only builds real LeRobot config objects from the unified platform config. It does not start hardware, connect to serial ports, load a real model checkpoint, or replace the existing constant-based `policy_server.py` / `robot_client.py` scripts.

## Verification

- `python3 -m unittest tests.test_lerobot_factory -v`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`
