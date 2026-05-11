# Quick Summary: Improve First Action Delta Diagnostics

Date: 2026-05-11
Status: Complete

## Changes

- First-frame safety rejection now reports:
  - joint key
  - leader action value
  - follower startup value
  - delta
  - configured threshold
- This helps align the specific SO-101 joint that caused a failure such as `36.088 > 25.000`.

## Verification

- Passed: `python3 -m unittest tests.test_tcp_teleop -v`
- Passed: `python3 scripts/run_server.py --config configs/teleop/remote_so101_tcp.yaml --dry-run`
- Passed: `git diff --check`
