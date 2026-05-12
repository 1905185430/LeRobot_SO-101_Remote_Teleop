# Phase 6: Package Architecture Generalization - Research

## RESEARCH COMPLETE

## Objective

Plan the migration from `so101_remote` to a fully layered `lerobot_remote` package without breaking the already validated SO-101 wireless TCP teleoperation, StarAI local TCP teleoperation, config-driven dry-runs, or thin LeRobot async entrypoints.

## Current Package Shape

The current implementation is concentrated under `so101_remote/`:

```text
so101_remote/
  adapters/
  network/
  client.py
  config.py
  config_loader.py
  config_schema.py
  dryrun.py
  lerobot_factory.py
  metrics.py
  recorder.py
  reliability.py
  runtime.py
  server.py
  starai.py
  teleop_tcp.py
  webui.py
```

Major responsibilities are mixed in a few broad modules:

- `runtime.py` handles dispatch, LeRobot async server/client, TCP teleop server/client startup, debug mock server/client, local mock loop, dashboard startup, run directory creation, config copying, and cleanup.
- `teleop_tcp.py` handles TCP leader client, TCP follower server, settings derivation, SO-101 builders, StarAI dispatch, action normalization, value validation, first-action safety, per-frame delta limiting, ACK handling, and timeout behavior.
- `starai.py` is already robot-specific and belongs under a robot layer.
- `metrics.py` and `recorder.py` are recording concerns.
- `config_loader.py` and `config_schema.py` are config concerns.
- `webui.py` combines dashboard state and Gradio app construction.

## Import Surface

Repository-owned imports currently reference `so101_remote` in:

- `policy_server.py`
- `robot_client.py`
- `scripts/run_server.py`
- `scripts/run_client.py`
- `scripts/run_local.py`
- all current unit tests covering config, runtime, metrics, recorder, webui, StarAI, TCP teleop, and LeRobot factories
- `README.md`
- `docs/validation/VALIDATION.md`
- `docs/project/PROJECT_CN.md`

Config names and run directory names also contain `so101_remote` strings, for example:

- `configs/remote_inference/so101_smolvla.yaml`
- `configs/teleop/remote_so101_tcp.yaml`

Those config experiment names describe the experiment, not the Python package. They do not have to be renamed in Phase 6 unless the user explicitly asks, because changing run directory names may disrupt reproducibility docs.

## Dirty Worktree Risk

There is an uncommitted user change in `so101_remote/config.py`:

```diff
-SERVER_ADDRESS = "192.168.1.10:8080"
+SERVER_ADDRESS = "192.168.1.151:8080"
```

Execution must preserve this change when moving `config.py` to `lerobot_remote/config/defaults.py` or equivalent. The executor must read `so101_remote/config.py` before moving or deleting it. Do not recreate the file from memory.

## Recommended Target Layout

Use the complete layered structure selected in `06-CONTEXT.md`:

```text
lerobot_remote/
  __init__.py

  config/
    __init__.py
    defaults.py
    loader.py
    schema.py

  runtime/
    __init__.py
    dispatch.py
    debug_mock.py
    remote_inference.py
    remote_teleop.py
    local_inference.py
    common.py

  teleop/
    __init__.py
    actions.py
    client.py
    safety.py
    server.py
    settings.py

  robots/
    __init__.py
    factory.py
    so101.py
    starai.py

  policies/
    __init__.py
    lerobot_async.py

  network/
    __init__.py
    protocol.py
    tcp_client.py
    tcp_server.py

  recording/
    __init__.py
    metrics.py
    recorder.py

  adapters/
    __init__.py
    lerobot_so101.py
    policy.py
    robot.py

  webui/
    __init__.py
    app.py
    state.py
```

`so101_remote/` should be removed as an implementation package. Since the user chose no compatibility shim, repository-owned imports must move to `lerobot_remote`. Historical mentions in planning docs may remain, but runtime code, tests, and operator docs should not tell users to import `so101_remote`.

## Split Recommendations

### Config

Move:

- `so101_remote/config.py` -> `lerobot_remote/config/defaults.py`
- `so101_remote/config_loader.py` -> `lerobot_remote/config/loader.py`
- `so101_remote/config_schema.py` -> `lerobot_remote/config/schema.py`

Use `lerobot_remote/config/__init__.py` to re-export common symbols:

- `ConfigError`
- `PlatformConfig`
- `load_config`
- `parse_simple_yaml`
- `platform_config_from_mapping`

### Recording

Move:

- `so101_remote/metrics.py` -> `lerobot_remote/recording/metrics.py`
- `so101_remote/recorder.py` -> `lerobot_remote/recording/recorder.py`

Update imports to `lerobot_remote.recording.metrics` and `lerobot_remote.recording.recorder`.

### Network

Move `so101_remote/network/` intact to `lerobot_remote/network/`.

### WebUI

Split:

- `DashboardState`, `snapshot_json` -> `lerobot_remote/webui/state.py`
- `launch_dashboard`, `render_dashboard_snapshot`, `render_images_html` -> `lerobot_remote/webui/app.py`

Re-export from `lerobot_remote/webui/__init__.py`.

### Robots

Move StarAI-specific code:

- `so101_remote/starai.py` -> `lerobot_remote/robots/starai.py`

Extract SO-101 builders from `teleop_tcp.py`:

- `build_so101_leader_device`
- `build_so101_follower_robot`
- `_build_lerobot_device_config`
- `_load_so101_leader_api`
- `_load_so101_follower_api`

to `lerobot_remote/robots/so101.py`.

Add `lerobot_remote/robots/factory.py` for:

- `SUPPORTED_TELEOP_FOLLOWER_TYPES`
- `SUPPORTED_TELEOP_LEADER_TYPES`
- `build_teleop_leader_device`
- `build_teleop_follower_robot`

This keeps teleop client/server logic independent of robot-specific construction.

### Policies

Move LeRobot async factory code:

- `so101_remote/lerobot_factory.py` -> `lerobot_remote/policies/lerobot_async.py`

It should import StarAI config construction from `lerobot_remote.robots.starai`. If desired, re-export common factory functions from `lerobot_remote/policies/__init__.py`.

### Teleop

Split `teleop_tcp.py`:

- `TcpTeleopSettings`, `tcp_teleop_settings` -> `lerobot_remote/teleop/settings.py`
- `normalize_teleop_action` -> `lerobot_remote/teleop/actions.py`
- `validate_action_values` and delta-related standalone helpers if extracted -> `lerobot_remote/teleop/safety.py`
- `TcpTeleopLeaderClient` -> `lerobot_remote/teleop/client.py`
- `TcpTeleopFollowerServer` -> `lerobot_remote/teleop/server.py`

Re-export public compatibility-within-new-package symbols from `lerobot_remote/teleop/__init__.py`, for example:

- `TcpTeleopFollowerServer`
- `TcpTeleopLeaderClient`
- `tcp_teleop_settings`
- `normalize_teleop_action`
- `validate_action_values`

Tests should import from new submodules where useful, but re-export tests are useful to keep ergonomics.

### Runtime

Split `runtime.py`:

- `configured_runtime_summary`, `run_configured_server`, `run_configured_client`, `run_configured_local` -> `lerobot_remote/runtime/dispatch.py`
- LeRobot async server/client runners and import helpers -> `lerobot_remote/runtime/remote_inference.py`
- TCP teleop server/client runners -> `lerobot_remote/runtime/remote_teleop.py`
- mock TCP server/client/local mock -> `lerobot_remote/runtime/debug_mock.py`
- shared run directory, metadata, config copy, dashboard launch, best-effort disconnect helpers -> `lerobot_remote/runtime/common.py`
- local inference not-implemented behavior -> `lerobot_remote/runtime/local_inference.py`

Re-export main runtime entrypoints from `lerobot_remote/runtime/__init__.py` so scripts can use:

```python
from lerobot_remote.runtime import configured_runtime_summary, run_configured_server
```

### Thin Async Entrypoints

Move:

- `so101_remote/client.py` -> `lerobot_remote/client.py`
- `so101_remote/server.py` -> `lerobot_remote/server.py`
- `so101_remote/dryrun.py` -> `lerobot_remote/dryrun.py`
- `so101_remote/reliability.py` -> `lerobot_remote/reliability.py`
- `so101_remote/adapters/` -> `lerobot_remote/adapters/`

Update `policy_server.py` and `robot_client.py` imports to `lerobot_remote`.

## Testing Strategy

Required automated checks from `06-CONTEXT.md`:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/run_server.py --config configs/teleop/remote_so101_tcp.yaml --dry-run
python3 scripts/run_client.py --config configs/teleop/remote_so101_tcp.yaml --dry-run
python3 scripts/run_server.py --config configs/teleop/local_starai_tcp.yaml --dry-run
python3 scripts/run_client.py --config configs/teleop/local_starai_tcp.yaml --dry-run
python3 scripts/run_server.py --config configs/debug/debug_mock_robot.yaml --dry-run
python3 scripts/run_client.py --config configs/debug/debug_mock_robot.yaml --dry-run
```

Additional static checks:

```bash
rg -n "from so101_remote|import so101_remote|so101_remote\\." \
  --glob '!logs/**' --glob '!runs/**' --glob '!**/__pycache__/**'
```

This static check should show no runtime code, scripts, tests, README, or operator docs with old imports. Historical `.planning/` references may remain if intentionally left as context.

## Main Risks

1. **Circular imports after splitting runtime and teleop.** Mitigate by keeping robot builders in `robots/`, settings/actions/safety in `teleop/`, and shared run helpers in `runtime/common.py`.
2. **Hidden stale imports in tests and docs.** Mitigate with `rg` check and full unit suite.
3. **Breaking top-level `policy_server.py` and `robot_client.py`.** Keep them thin and update only imports.
4. **Losing user-local `SERVER_ADDRESS` change in `config.py`.** Move the actual file content rather than recreating it.
5. **Over-claiming hardware validation.** Keep docs clear: Phase 6 requires automated tests and dry-runs, not fresh hardware reruns.
6. **Generated artifacts polluting migration.** Ignore `logs/`, `runs/`, `map.png`, and `__pycache__/` during planning and execution unless user explicitly asks otherwise.

## Suggested Plan Breakdown

1. Build the new `lerobot_remote` package skeleton and move low-coupling foundation modules: config, recording, network, adapters, dryrun, reliability, webui state/app.
2. Extract robot, policy, and teleop modules: SO-101 builders, StarAI support, LeRobot async policy factories, teleop settings/actions/safety/client/server.
3. Split runtime orchestration and update all entrypoint imports.
4. Update tests and docs, remove old implementation package, run verification commands, and record results.

## Validation Architecture

Phase 6 validation should require:

- import-level proof: tests import from `lerobot_remote`, not `so101_remote`;
- behavior proof: all existing unit tests pass;
- CLI proof: dry-run commands for SO-101, StarAI, and debug mock configs pass;
- migration proof: repository-owned runtime/test/doc imports no longer reference `so101_remote`;
- safety proof: docs still identify real hardware reruns as manual validation, not as automatically completed by refactor.
