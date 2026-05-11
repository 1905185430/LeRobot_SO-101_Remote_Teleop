# SO-101 LeRobot Async Inference Playground

This repo is now set up for the smallest possible LeRobot async inference workflow while you explore SmolVLA wireless inference:

- run `policy_server.py` on the server or GPU machine
- run `robot_client.py` on the robot-side computer
- keep `legacy/` around as the old custom UDP teleop reference

There is no local config layer in the main path now. You edit a few constants at the top of each file and run them directly.

## Install

Install LeRobot with async inference support on both machines. Follow the official LeRobot install instructions for your version.

Before real hardware experiments, use [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) to check the GPU server, robot-side computer, LAN connectivity, time synchronization, and common failure cases.

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

## Experiment Artifacts

Phase 2 stores local experiment runs under `logs/experiments/<run_id>/` by default.
The run artifact set is:

- `metadata.json`
- `metrics.jsonl`
- `events.jsonl`
- `metrics.csv`
- `summary.md`

Real LeRobot runtime hooks are wired in later phases; this artifact layout is the local contract those hooks will write into.

## SO-101 Notes

- `ROBOT_ID` must match your follower calibration id.
- Camera keys in `CAMERAS` must match the keys expected by the model you trained or downloaded.
- `TASK` should stay close to the instruction wording used in your data collection or fine-tuning.
- `ACTIONS_PER_CHUNK` should not exceed what the policy supports.

## Legacy

The old custom UDP teleop path is still under `legacy/`, but it is no longer the recommended path for inference experiments.

Run tests with:

```bash
python3 -m unittest discover -s tests -v
```
