---
quick_id: 260511-pxi
slug: wire-config-driven-real-and-mock-runtime
type: quick
status: planned
requirements: []
must_haves:
  truths:
    - "Config-driven client/server scripts run real LeRobot async inference for remote_inference when LeRobot is installed."
    - "Config-driven debug_mock mode exercises the local TCP protocol without hardware."
    - "Unsupported modes fail explicitly instead of pretending to be complete."
    - "Chinese project guide explains architecture, usage, debugging, and current boundaries."
  artifacts:
    - path: "so101_remote/runtime.py"
      provides: "Config-driven runtime dispatch for real LeRobot and mock TCP paths"
    - path: "docs/PROJECT_CN.md"
      provides: "Chinese project guide"
---

# Quick Task: Wire config-driven real and mock runtime

## Scope

Connect the unified config layer to executable client/server entrypoints. Keep this phase focused on the first real path, SO-101 + SmolVLA remote inference through LeRobot async inference, plus a hardware-free TCP mock path for debugging.

## Tasks

1. Add runtime dispatch module.
   - Files: `so101_remote/runtime.py`
   - Verify: fake LeRobot tests can run server/client paths without installing LeRobot.

2. Wire scripts to runtime.
   - Files: `scripts/run_client.py`, `scripts/run_server.py`, `scripts/run_local.py`
   - Verify: dry-run behavior remains unchanged and non-dry-run no longer raises placeholder errors for supported paths.

3. Add Chinese project guide.
   - Files: `docs/PROJECT_CN.md`, `README.md`
   - Verify: guide includes architecture, command usage, config editing, debug workflow, and current limitations.

4. Run regression tests.
   - Verify: `python3 -m unittest discover -s tests -v` and `git diff --check`.
