---
quick_id: 260511-pix
slug: add-unified-config-loader-and-script-ent
type: quick
status: planned
requirements: []
must_haves:
  truths:
    - "A unified config loader can load named YAML configs and validate mode/model/robot/network/runtime sections without LeRobot installed."
    - "Sample configs exist for local inference, remote inference, remote teleoperation, and mock debugging."
    - "Thin script entrypoints exist for client, server, and local modes and can dry-run config loading without hardware."
    - "Existing tests still pass and new config tests cover schema behavior."
  artifacts:
    - path: "so101_remote/config_schema.py"
      provides: "Dataclass schema and validation for platform configs"
    - path: "so101_remote/config_loader.py"
      provides: "YAML loading and config resolution"
    - path: "scripts/run_client.py"
      provides: "Client entrypoint for config-driven remote modes"
    - path: "scripts/run_server.py"
      provides: "Server entrypoint for config-driven remote modes"
    - path: "scripts/run_local.py"
      provides: "Local inference entrypoint for baseline mode"
---

# Quick Task: Add unified config loader and script entrypoints

## Scope

Implement the first code layer for the new platform requirements: config schema/loader, sample YAML configs, and dry-run-capable script entrypoints. Do not implement real TCP transport, WebUI, or hardware behavior in this quick task.

## Tasks

1. Add config schema and loader modules.
   - Files: `so101_remote/config_schema.py`, `so101_remote/config_loader.py`, `so101_remote/__init__.py`
   - Verify: unit tests can load sample configs and reject invalid mode/protocol values.

2. Add sample configs and script entrypoints.
   - Files: `configs/*.yaml`, `scripts/run_client.py`, `scripts/run_server.py`, `scripts/run_local.py`
   - Verify: scripts support `--config` and `--dry-run` and print resolved mode/config summary.

3. Add tests and docs.
   - Files: `tests/test_config_loader.py`, `README.md`
   - Verify: `python3 -m unittest discover -s tests -v` and `git diff --check` pass.
