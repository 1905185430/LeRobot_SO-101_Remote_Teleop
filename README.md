# lerobot-remote-vla-teleop

This repo is a lightweight LeRobot remote VLA inference and TCP teleoperation experiment framework. It started from SO-101 + SmolVLA wireless inference, and now also records validated TCP teleoperation paths for SO-101 and StarAI arms.

If the architecture feels unclear, start with the Chinese architecture guide:

- [docs/ARCHITECTURE_CN.md](docs/ARCHITECTURE_CN.md)

Experiments are config-driven. Use the scripts under `scripts/` and YAML files under `configs/`.

Recommended paths:

- TCP teleoperation: `scripts/run_teleop_follower.py` and `scripts/run_teleop_leader.py`
- Remote VLA inference: `scripts/run_server.py` and `scripts/run_client.py`

The implementation package is now `lerobot_remote/`. It is split by responsibility into config, runtime, teleop, robots, policies, network, recording, and WebUI modules.

## Install

Install LeRobot with async inference support on both machines. Follow the official LeRobot install instructions for your version.

Before real hardware experiments, use [docs/setup/ENVIRONMENT.md](docs/setup/ENVIRONMENT.md) to check the GPU server, robot-side computer, LAN connectivity, time synchronization, and common failure cases. For a Chinese project-level guide, see [docs/project/PROJECT_CN.md](docs/project/PROJECT_CN.md).

## Validation Status

See [docs/validation/VALIDATION.md](docs/validation/VALIDATION.md) for the current validation matrix. The automated suite proves unit-only and dry-run readiness, but it does not prove real SO-101 hardware, camera frames, SmolVLA model loading, physical control-loop stability, or 10-30 minute LAN endurance.

## Run: Config-Driven Paths

Validate a local inference config without touching hardware:

```bash
python3 scripts/run_local.py --config configs/local_inference/so101_smolvla.yaml --dry-run
```

Validate the remote inference server/client configs:

```bash
python3 scripts/run_server.py --config configs/remote_inference/so101_smolvla.yaml --dry-run
python3 scripts/run_client.py --config configs/remote_inference/so101_smolvla.yaml --dry-run
```

Run remote inference:

```bash
# GPU/server machine
python3 scripts/run_server.py --config configs/remote_inference/so101_smolvla.yaml

# robot-side machine
python3 scripts/run_client.py --config configs/remote_inference/so101_smolvla.yaml
```

Run TCP teleoperation:

```bash
# follower/server machine
python3 scripts/run_teleop_follower.py --config configs/teleop/remote_so101_tcp.yaml

# leader/client machine
python3 scripts/run_teleop_leader.py --config configs/teleop/remote_so101_tcp.yaml
```

The generic commands still work for teleoperation, but the role-explicit commands are easier to read:

```bash
python3 scripts/run_server.py --config configs/teleop/remote_so101_tcp.yaml
python3 scripts/run_client.py --config configs/teleop/remote_so101_tcp.yaml
```

## Additional Dry-Runs

Validate teleoperation configs:

```bash
python3 scripts/run_teleop_follower.py --config configs/teleop/remote_so101_tcp.yaml --dry-run
python3 scripts/run_teleop_leader.py --config configs/teleop/remote_so101_tcp.yaml --dry-run
python3 scripts/run_teleop_follower.py --config configs/teleop/remote_starai_tcp.yaml --dry-run
python3 scripts/run_teleop_leader.py --config configs/teleop/remote_starai_tcp.yaml --dry-run
```

Config-driven scripts now support these executable paths:

- `remote_inference` builds real LeRobot async inference server/client configs for the first supported path, SO-101 follower + SmolVLA.
- `remote_teleoperation` runs a config-driven TCP leader/follower action stream for SO-101 and StarAI.
- StarAI arms are supported through LeRobot-backed type names such as `lerobot_robot_viola`, `lerobot_robot_cello`, and `lerobot_teleoperator_violin`, plus aliases like `starai_viola_follower` and `starai_violin_leader`.
- `debug_mock` runs a hardware-free TCP mock observation/action round trip.
- Server-side `webui.enabled: true` launches an optional Gradio dashboard when Gradio is installed; if Gradio is missing, runtime startup continues and records a warning event.

`local_inference` and real LeRobot observation streaming into WebUI are still explicit next steps. The config layer exposes LeRobot object construction through `lerobot_remote.policies.lerobot_async` and keeps lazy imports, so tests can run without LeRobot installed.

## Package Layout

```text
lerobot_remote/
  config/       defaults, YAML/JSON loader, schema validation
  runtime/      dispatch, remote inference, teleoperation, debug mock loops
  teleop/       TCP leader/client, follower/server, action normalization, safety checks
  robots/       SO-101 and StarAI builders plus robot factory dispatch
  policies/     LeRobot async policy/client config builders
  network/      length-prefixed TCP protocol helpers
  recording/    metrics, run directory, metadata, CSV/summary artifacts
  webui/        optional Gradio dashboard state and rendering
```

## TCP Protocol

The first TCP layer lives in `lerobot_remote.network`. It uses a 4-byte big-endian length header followed by one JSON payload:

```text
[4-byte message length][JSON payload]
```

Supported message types are `OBSERVATION`, `ACTION`, `HEARTBEAT`, `RESET`, `STOP`, `ERROR`, and `ACK`. The current TCP teleoperation path uses `ACTION`/`ACK`; debug mock uses `OBSERVATION`/`ACTION`. Image bytes, msgpack, real policy image streaming, and richer WebUI streaming are later work.

## Experiment Artifacts

Phase 2 stores local experiment runs under `logs/experiments/<run_id>/` by default.
The run artifact set is:

- `metadata.json`
- `metrics.jsonl`
- `events.jsonl`
- `metrics.csv`
- `summary.md`

Real LeRobot remote inference and TCP teleoperation paths write into this artifact layout.

## Real Runtime Artifacts

When you run the config-driven real paths, each side creates its own run directory under `experiment.save_dir`.

- `python3 scripts/run_server.py --config ...` creates a server-role run directory such as `policy-server` or `tcp-teleop-follower`.
- `python3 scripts/run_client.py --config ...` creates a client-role run directory such as `robot-client` or `tcp-teleop-leader`.

Each real runtime run directory includes:

- `metadata.json`
- `events.jsonl`
- `summary.md`

The metadata records the role, endpoint, model/policy or robot fields available to that side, the run directory, and the resolved settings used at startup. Config-driven scripts also copy the selected YAML into the run directory as `config.yaml`.

## Dry Run

Run a local dry-run without SO-101 hardware or LeRobot:

```bash
python3 -c "from lerobot_remote.dryrun import run_dry_run; print(run_dry_run())"
```

Dry-run validates the code path, metrics plumbing, and artifact generation only.
It does not validate real SO-101 hardware, camera frames, real SmolVLA loading, inference quality, or physical safety behavior.

## SO-101 Notes

- `robot.id` must match your follower calibration id.
- Camera keys in `camera.cameras` must match the keys expected by the model you trained or downloaded.
- `experiment.task_name` should stay close to the instruction wording used in your data collection or fine-tuning.
- `model.action_horizon` should not exceed what the policy supports.

Run tests with:

```bash
python3 -m unittest discover -s tests -v
```
