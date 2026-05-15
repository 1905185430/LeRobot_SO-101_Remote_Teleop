# AGENTS.md instructions for this repository

## Project

**SO-101 / StarAI Remote VLA Inference And TCP Teleoperation Experiments**

This repository is a lightweight LeRobot experiment framework centered on config-driven remote VLA inference and TCP teleoperation.

The current mainline is:

- config-driven scripts under `scripts/`;
- YAML configs under `configs/`;
- implementation package `lerobot_remote/`;
- structured run artifacts under configured `experiment.save_dir`.

Legacy UDP teleoperation and root constant-based compatibility entrypoints have been removed. Do not recreate them unless the user explicitly asks for a separate migration or recovery task.

## Current Main Paths

### Remote Inference

- Server/GPU side:
  - `python3 scripts/run_server.py --config configs/remote_inference/so101_smolvla.yaml`
- Robot-side client:
  - `python3 scripts/run_client.py --config configs/remote_inference/so101_smolvla.yaml`

### TCP Teleoperation

- Follower side:
  - `python3 scripts/run_teleop_follower.py --config configs/teleop/local_starai_tcp.yaml`
- Leader side:
  - `python3 scripts/run_teleop_leader.py --config configs/teleop/local_starai_tcp.yaml`

The generic `run_server.py` / `run_client.py` scripts still dispatch `remote_teleoperation`, but role-explicit teleop scripts are preferred for operator clarity.

## Package Map

- `lerobot_remote/config/`: YAML/JSON loading and schema validation.
- `lerobot_remote/runtime/`: mode dispatch, remote inference orchestration, TCP teleoperation orchestration, debug mock loops.
- `lerobot_remote/teleop/`: TCP leader/follower loops, action normalization, safety checks, settings.
- `lerobot_remote/robots/`: SO-101 and StarAI robot/teleoperator builders.
- `lerobot_remote/policies/`: LeRobot async inference config builders.
- `lerobot_remote/network/`: length-prefixed TCP protocol helpers.
- `lerobot_remote/recording/`: run directories, metadata, metrics, events, summaries.
- `lerobot_remote/webui/`: optional dashboard state and rendering.

## Development Rules

- Prefer config-driven changes over hard-coded constants.
- Keep hardware-facing failures visible in logs and run artifacts.
- Do not silently weaken teleoperation safety limits.
- Preserve validated StarAI and SO-101 TCP teleoperation commands.
- Keep generated runtime artifacts out of git.
- Use `python3 -m unittest discover -s tests -v` for the full automated suite.

## Documentation

Start here when the architecture is unclear:

- `docs/ARCHITECTURE_CN.md`
- `docs/reproduction/STARAI_LOCAL_TCP_TELEOP.md`
- `docs/reproduction/SO101_WIRELESS_TCP_TELEOP.md`
- `docs/setup/ENVIRONMENT.md`
- `docs/validation/VALIDATION.md`

## GSD Workflow

Before editing files, start work through a GSD command so planning artifacts and execution context stay in sync.

Use:

- `/gsd-quick` for small fixes, docs, and ad-hoc cleanup;
- `/gsd-debug` for investigation and bug fixing;
- `/gsd-execute-phase` for planned phase work.
