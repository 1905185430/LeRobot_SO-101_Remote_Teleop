# lerobot-remote-vla-teleop

Lightweight LeRobot experiments for remote VLA inference and TCP teleoperation.

Current mainline:

- config-driven scripts in `scripts/`
- YAML configs in `configs/`
- implementation package `lerobot_remote/`
- run artifacts under each config's `experiment.save_dir`

## Start Here

- Architecture guide: [docs/ARCHITECTURE_CN.md](docs/ARCHITECTURE_CN.md)
- Environment setup: [docs/setup/ENVIRONMENT.md](docs/setup/ENVIRONMENT.md)
- Reproduction index: [docs/reproduction/REPRODUCTION.md](docs/reproduction/REPRODUCTION.md)
- Validation boundaries: [docs/validation/VALIDATION.md](docs/validation/VALIDATION.md)

## Main Commands

Remote VLA inference:

```bash
# GPU / policy server
python3 scripts/run_server.py --config configs/remote_inference/so101_smolvla.yaml

# robot-side client
python3 scripts/run_client.py --config configs/remote_inference/so101_smolvla.yaml
```

TCP teleoperation:

```bash
# follower side
python3 scripts/run_teleop_follower.py --config configs/teleop/remote_so101_tcp.yaml

# leader side
python3 scripts/run_teleop_leader.py --config configs/teleop/remote_so101_tcp.yaml
```

Dry-run examples:

```bash
python3 scripts/run_server.py --config configs/remote_inference/so101_smolvla.yaml --dry-run
python3 scripts/run_client.py --config configs/remote_inference/so101_smolvla.yaml --dry-run
python3 scripts/run_teleop_follower.py --config configs/teleop/local_starai_tcp.yaml --dry-run
python3 scripts/run_teleop_leader.py --config configs/teleop/local_starai_tcp.yaml --dry-run
```

Run tests:

```bash
python3 -m unittest discover -s tests -v
```

## Package Map

```text
lerobot_remote/
  config/       config loading and schema validation
  runtime/      mode dispatch and runtime orchestration
  teleop/       TCP teleoperation loops, safety, action normalization
  robots/       SO-101 and StarAI builders
  policies/     LeRobot async config builders
  network/      length-prefixed TCP protocol helpers
  recording/    metrics, events, run directories, summaries
  webui/        optional dashboard state and rendering
```
