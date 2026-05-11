---
quick_id: 260511-sxo
slug: add-starai-leader-read-safety-diagnostic
type: quick
status: complete
completed_at: 2026-05-11
---

# Quick Task Summary: Add StarAI leader read safety diagnostics

## Completed

- Added `TcpTeleopLeaderClient.read_safe_leader_action()`.
- Leader-side `get_action()` failures now stop before sending any command to follower.
- Error message now points to leader serial port, power, motor IDs, calibration, and StarAI/FashionStar SDK hotfixes.
- Added regression test for wrapping the observed `NoneType >= int` read failure.

## Verification

- `python3 -m unittest tests.test_tcp_teleop -v`
- `python3 -m unittest discover -s tests -v`
