# SO-101 LeRobot Async Inference Playground

This repo is now set up for the smallest possible LeRobot async inference workflow while you explore SmolVLA wireless inference:

- run `policy_server.py` on the server or GPU machine
- run `robot_client.py` on the robot-side computer
- keep `legacy/` around as the old custom UDP teleop reference

There is no local config layer in the main path now. You edit a few constants at the top of each file and run them directly.

The next platform layer has started: `configs/*.yaml` plus `scripts/run_client.py`, `scripts/run_server.py`, and `scripts/run_local.py` can validate named platform configs with `--dry-run`. The real LeRobot runtime still uses the existing thin entrypoints until the TCP/WebUI runners are implemented.

## Install

Install LeRobot with async inference support on both machines. Follow the official LeRobot install instructions for your version.

Before real hardware experiments, use [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) to check the GPU server, robot-side computer, LAN connectivity, time synchronization, and common failure cases. For a Chinese project-level guide, see [docs/PROJECT_CN.md](docs/PROJECT_CN.md).

## Validation Status

See [docs/VALIDATION.md](docs/VALIDATION.md) for the current validation matrix. The automated suite proves unit-only, dry-run-only, and retained legacy compatibility readiness, but it does not prove real SO-101 hardware, camera frames, SmolVLA model loading, physical control-loop stability, or 10-30 minute LAN endurance.

## Run

On the server or GPU machine:

```bash
python3 policy_server.py
```

Before running it, edit these constants in [policy_server.py](/home/xuan/Documents/VLA+无线通信/LeRobot_SO-101_Remote_Teleop/policy_server.py:5):

- `HOST`
- `PORT`

On the robot-side machine:

```bash
python3 robot_client.py
```

Before running it, edit these constants in [robot_client.py](/home/xuan/Documents/VLA+无线通信/LeRobot_SO-101_Remote_Teleop/robot_client.py:8):

- `SERVER_ADDRESS`
- `ROBOT_PORT`
- `ROBOT_ID`
- `CAMERAS`
- `TASK`
- `POLICY_TYPE`
- `PRETRAINED_NAME_OR_PATH`
- `POLICY_DEVICE`
- `ACTIONS_PER_CHUNK`
- `CHUNK_SIZE_THRESHOLD`
- `AGGREGATE_FN_NAME`
- `DEBUG_VISUALIZE_QUEUE_SIZE`

## Config-Driven Platform Preview

Validate a local inference config without touching hardware:

```bash
python3 scripts/run_local.py --config configs/local_inference_so101_smolvla.yaml --dry-run
```

Validate the remote inference server/client configs:

```bash
python3 scripts/run_server.py --config configs/remote_inference_so101_smolvla.yaml --dry-run
python3 scripts/run_client.py --config configs/remote_inference_so101_smolvla.yaml --dry-run
```

Validate the remote teleoperation config:

```bash
python3 scripts/run_server.py --config configs/remote_teleop_so101_tcp.yaml --dry-run
python3 scripts/run_client.py --config configs/remote_teleop_so101_tcp.yaml --dry-run
```

Config-driven scripts now support two executable paths:

- `remote_inference` builds real LeRobot async inference server/client configs for the first supported path, SO-101 follower + SmolVLA.
- `debug_mock` runs a hardware-free TCP mock observation/action round trip.

`local_inference`, config-driven TCP teleoperation, and WebUI rendering are still explicit next steps. The config layer exposes LeRobot object construction through `so101_remote.lerobot_factory` and keeps lazy imports, so tests can run without LeRobot installed.

## TCP Protocol Preview

The first TCP layer lives in `so101_remote.network`. It uses a 4-byte big-endian length header followed by one JSON payload:

```text
[4-byte message length][JSON payload]
```

Supported message types are `OBSERVATION`, `ACTION`, `HEARTBEAT`, `RESET`, `STOP`, `ERROR`, and `ACK`. The current implementation is a testable mock layer for protocol and client/server round trips; image bytes, msgpack, real policy inference, and WebUI streaming are later work.

## Experiment Artifacts

Phase 2 stores local experiment runs under `logs/experiments/<run_id>/` by default.
The run artifact set is:

- `metadata.json`
- `metrics.jsonl`
- `events.jsonl`
- `metrics.csv`
- `summary.md`

Real LeRobot runtime hooks are wired in later phases; this artifact layout is the local contract those hooks will write into.

## Real Runtime Artifacts

When you run the real thin entrypoints, each side creates its own run directory under `logs/experiments/`.

- `python3 policy_server.py` creates a `policy-server` run directory for the GPU/server process.
- `python3 robot_client.py` creates a `robot-client` run directory for the robot-side process.

Each real runtime run directory includes:

- `metadata.json`
- `events.jsonl`
- `summary.md`

The metadata records the role, endpoint, model/policy or robot fields available to that side, the run directory, and the resolved constant settings used at startup. For v1, constants in `policy_server.py` and `robot_client.py` remain the configuration path; there is no YAML or CLI override layer required for Phase 4.

## Dry Run

Run a local dry-run without SO-101 hardware or LeRobot:

```bash
python3 -c "from so101_remote.dryrun import run_dry_run; print(run_dry_run())"
```

Dry-run validates the code path, metrics plumbing, and artifact generation only.
It does not validate real SO-101 hardware, camera frames, real SmolVLA loading, inference quality, or physical safety behavior.

## SO-101 Notes

- `ROBOT_ID` must match your follower calibration id.
- Camera keys in `CAMERAS` must match the keys expected by the model you trained or downloaded.
- `TASK` should stay close to the instruction wording used in your data collection or fine-tuning.
- `ACTIONS_PER_CHUNK` should not exceed what the policy supports.

## Legacy

The old custom UDP teleop path is still under `legacy/`. It is retained compatibility/reference code and not the v1 main runtime path for inference experiments.

Run tests with:

```bash
python3 -m unittest discover -s tests -v
```
