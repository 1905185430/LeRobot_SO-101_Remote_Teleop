---
quick_id: 260511-qzk
slug: add-tcp-teleop-action-delta-safety-limit
type: quick
status: complete
completed_at: 2026-05-11
---

# Quick Task Summary: Add TCP teleop action delta safety limit

## Completed

- Added follower startup position capture through `get_observation()` when available.
- Added per-frame action delta limiting before `send_action()`.
- Default max action delta is `2.0` normalized units per frame.
- Added tests for large first target clamping.

## Verification

- `python3 -m unittest tests.test_tcp_teleop -v`
- `python3 -m unittest tests.test_starai -v`
- `python3 -m unittest discover -s tests -v`
