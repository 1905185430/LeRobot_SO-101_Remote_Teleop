---
quick_id: 260511-qme
slug: add-local-starai-tcp-teleoperation-confi
type: quick
status: complete
completed_at: 2026-05-11
---

# Quick Task Summary: Add local StarAI TCP teleoperation config

## Completed

- Added `configs/local_teleop_starai_tcp.yaml`.
- Set `network.server_host` to `127.0.0.1` for same-machine TCP teleoperation.
- Used separate TCP and WebUI ports from the remote StarAI example.
- Verified both server and client dry-run entrypoints.

## Verification

- `python3 scripts/run_server.py --config configs/local_teleop_starai_tcp.yaml --dry-run`
- `python3 scripts/run_client.py --config configs/local_teleop_starai_tcp.yaml --dry-run`
- `git diff --check`
