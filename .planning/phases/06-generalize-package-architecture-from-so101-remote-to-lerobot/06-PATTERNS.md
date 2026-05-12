# Phase 6: Pattern Map

## Closest Existing Analogs

| New area | Current source | Closest analog / pattern |
| --- | --- | --- |
| `lerobot_remote/config/loader.py` | `so101_remote/config_loader.py` | Pure loader module with explicit `ConfigError`; no LeRobot import. |
| `lerobot_remote/config/schema.py` | `so101_remote/config_schema.py` | Frozen dataclass schema objects and section parsers. |
| `lerobot_remote/config/defaults.py` | `so101_remote/config.py` | Constant-based v1 settings used by `client.py` and `server.py`. Preserve dirty local value. |
| `lerobot_remote/recording/metrics.py` | `so101_remote/metrics.py` | Data model and aggregation helpers with no hardware dependency. |
| `lerobot_remote/recording/recorder.py` | `so101_remote/recorder.py` | Run directory and JSONL/CSV recorder boundary. |
| `lerobot_remote/network/*` | `so101_remote/network/*` | Length-prefixed TCP protocol package can move mostly intact. |
| `lerobot_remote/robots/starai.py` | `so101_remote/starai.py` | Lazy import, type alias sets, config construction, startup pose override. |
| `lerobot_remote/robots/so101.py` | SO-101 builder functions in `so101_remote/teleop_tcp.py` | Lazy module-path compatibility for SO-101 leader/follower APIs. |
| `lerobot_remote/robots/factory.py` | `build_teleop_*` dispatch in `so101_remote/teleop_tcp.py` | Central robot type dispatch for teleop runtime. |
| `lerobot_remote/policies/lerobot_async.py` | `so101_remote/lerobot_factory.py` | LeRobot async config factory with lazy imports. |
| `lerobot_remote/teleop/*` | `so101_remote/teleop_tcp.py` | Split by settings/actions/safety/client/server. |
| `lerobot_remote/runtime/*` | `so101_remote/runtime.py` | Split by dispatch, mode-specific runners, shared helpers. |
| `lerobot_remote/webui/state.py` | `DashboardState` in `so101_remote/webui.py` | Thread-safe state dataclass. |
| `lerobot_remote/webui/app.py` | render/launch helpers in `so101_remote/webui.py` | Optional Gradio import and rendering helpers. |

## Import Patterns To Preserve

- Keep lazy LeRobot imports inside runtime/build functions rather than module import time.
- Keep thin scripts by importing from package-level stable module APIs:
  - `lerobot_remote.config`
  - `lerobot_remote.runtime`
- Use `__init__.py` re-exports for new subpackages where tests and scripts need ergonomic imports.
- Do not add a `so101_remote` shim, because the user chose a clean break.

## Specific Extraction Boundaries

### Teleop

Move public teleop symbols into submodules:

- `TcpTeleopSettings` and `tcp_teleop_settings` -> `teleop/settings.py`
- `TcpTeleopLeaderClient` -> `teleop/client.py`
- `TcpTeleopFollowerServer` -> `teleop/server.py`
- `normalize_teleop_action` -> `teleop/actions.py`
- `validate_action_values` -> `teleop/safety.py`

`teleop/server.py` should import `validate_action_values` and `normalize_teleop_action`, but should not import robot-specific builders. Robot builders belong in `robots/factory.py` and runtime code composes both.

### Runtime

Use `runtime/common.py` for helpers shared by all runners:

- `_build_configured_metadata`
- `_create_configured_run_dir`
- `_copy_source_config`
- `_maybe_launch_dashboard`
- `_disconnect_best_effort`
- `_mock_joint_positions`

Then split runners:

- `runtime/dispatch.py`: `configured_runtime_summary`, `run_configured_server`, `run_configured_client`, `run_configured_local`
- `runtime/remote_inference.py`: `run_lerobot_policy_server`, `run_lerobot_robot_client`
- `runtime/remote_teleop.py`: `run_tcp_teleop_follower_server`, `run_tcp_teleop_leader_client`
- `runtime/debug_mock.py`: `run_mock_tcp_server`, `run_mock_tcp_client`, `run_local_mock_loop`
- `runtime/local_inference.py`: current not-implemented `local_inference` behavior

### Robots And Policies

Move StarAI support to `robots/starai.py` without changing behavior. Extract SO-101 teleop builders to `robots/so101.py`.

Move LeRobot async config factory to `policies/lerobot_async.py`. This module may still build robot configs, but should import robot-specific config builders from `robots/`.

## Test Patterns To Preserve

- Tests currently fake LeRobot modules through `mock.patch.dict(sys.modules, ...)`; keep lazy import locations so this remains possible.
- `tests/test_tcp_teleop.py` covers action safety and runtime dispatch patching. Update patches from `so101_remote.runtime...` to new module locations.
- `tests/test_starai.py` covers StarAI type detection, config construction, calibration dirs, and startup move suppression.
- `tests/test_minimal_async_scripts.py` covers top-level thin entrypoints.
- `tests/test_config_loader.py`, `tests/test_lerobot_factory.py`, `tests/test_configured_runtime.py`, `tests/test_webui.py`, and network/recording tests cover import paths likely affected by this split.

## Verification Patterns

Use exact verification commands from `06-CONTEXT.md`.

Additionally, use static import checks:

```bash
rg -n "from so101_remote|import so101_remote|so101_remote\\." \
  --glob '!logs/**' --glob '!runs/**' --glob '!**/__pycache__/**' \
  README.md docs scripts tests policy_server.py robot_client.py lerobot_remote
```

This should return no results after Phase 6, except if a plan explicitly documents a historical reference outside these runtime/test/operator surfaces.
