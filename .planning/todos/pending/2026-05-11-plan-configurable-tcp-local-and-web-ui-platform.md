---
created: 2026-05-11T10:16:33.152Z
title: Plan configurable TCP local and web UI platform
area: planning
files:
  - .planning/ROADMAP.md
  - .planning/PROJECT.md
  - .planning/REQUIREMENTS.md
  - so101_remote/config.py
  - policy_server.py
  - robot_client.py
  - legacy/
  - docs/
  - README.md
---

## Problem

Future work needs to evolve the current SO-101 + SmolVLA experiment framework into a configurable remote VLA / teleoperation platform while still staying grounded in LeRobot. The platform should not be just a remote-control script; it should become a lightweight LeRobot-based experiment framework for local inference, remote inference, remote teleoperation, metrics, run artifacts, and live visualization.

The target positioning is:

- SO-101 first, but structured so other robot arms can be added later.
- ACT, SmolVLA, Pi0/PI-series, and mock policies should fit behind policy/config boundaries.
- The same project should support baseline local inference, TCP remote inference, TCP remote teleoperation, and later dataset recording.
- The server side should provide observability through a WebUI for images, joint state, model action, latency, inference time, logs, and safety state.

Baseline requirements:

- Support a local single-machine inference option that does not involve wireless networking.
- Keep the internal runtime based on the LeRobot framework.
- Use TCP for the two-host path, with both hosts on the same LAN or a virtual LAN such as Tailscale.
- Keep a `client` Python program and a `server` Python program.
- Add a unified config entry point that selects model, robot arm type, operation mode, and task-specific settings.
- Support multiple selectable configs for different tasks.
- Make operation mode explicit, such as `local_inference`, `remote_inference`, `remote_teleoperation`, `data_recording`, or later modes.
- Save enough run artifacts for experiment comparison and papers: config, metrics, events, actions, images/videos when enabled, and summaries.

The current v1 code intentionally keeps constants lightweight. That was appropriate for the first working path, but the next milestone needs a proper configuration and runtime-mode design before adding more robots, teleoperation modes, or model backends.

## Solution

Use this todo as the design seed for the next milestone. Likely architecture:

- Design a YAML config system with schema validation and named config files under `configs/`.
- Define runtime modes such as `local_inference`, `remote_inference`, `remote_teleoperation`, `data_recording`, and debug/mock modes.
- Decide how the TCP server/client boundary maps to LeRobot async inference and whether to keep current top-level `policy_server.py` / `robot_client.py` as compatibility wrappers around new scripts.
- Keep SO-101 + SmolVLA as the reference config while adding extension points for other arms and policies.
- Add a length-prefixed TCP protocol so observation/action payloads do not suffer from TCP sticky-packet or split-packet bugs.
- Start with TCP + msgpack + JPEG bytes for remote inference, while allowing simpler JSON/base64 during early debugging if needed.
- Build mock robot and mock policy paths first so client/server/protocol can be tested without hardware.

Suggested commands after implementation:

```bash
python scripts/run_local.py --config configs/local_inference_so101_smolvla.yaml
python scripts/run_server.py --config configs/remote_inference_so101_smolvla.yaml
python scripts/run_client.py --config configs/remote_inference_so101_smolvla.yaml
python scripts/run_server.py --config configs/remote_teleop_so101_tcp.yaml
python scripts/run_client.py --config configs/remote_teleop_so101_tcp.yaml
python scripts/record_dataset.py --config configs/data_recording_so101_multicam.yaml
```

Suggested config files:

- `configs/local_inference_so101_act.yaml`
- `configs/local_inference_so101_smolvla.yaml`
- `configs/remote_inference_so101_smolvla.yaml`
- `configs/remote_teleop_so101_tcp.yaml`
- `configs/data_recording_so101_multicam.yaml`
- `configs/debug_mock_robot.yaml`
- `configs/debug_no_camera.yaml`

Suggested config sections:

- `experiment`: name, mode, task name, save directory.
- `robot`: robot type, port, id, calibration directory.
- `teleop`: leader type, port, id, enabled flag.
- `model`: model type, model path, device, dtype, action horizon, inference frequency.
- `camera`: camera list, type, index/path, resolution, fps.
- `network`: protocol, server host, port, timeout, reconnect, max packet size.
- `runtime`: control frequency, observation frequency, action send frequency, timeout behavior.
- `webui`: enabled flag, host, port, images, joint states, latency, actions.
- `logging`: save video, metrics, observations, actions, log level.

## Runtime Modes

### `local_inference`

All hardware, cameras, and model inference run on one machine. This is the baseline and should be used before remote experiments.

Purpose:

- Validate camera, robot, and model without network variables.
- Establish the lowest-latency performance ceiling.
- Provide the local baseline for remote inference comparison.

### `remote_inference`

Client reads cameras and robot state, sends observation to a GPU/server process over TCP, receives action, and executes on the SO-101 follower.

Client responsibilities:

- Read camera images.
- Read SO-101 joint state.
- Package observation with timestamps and frame ids.
- Send observation to server.
- Receive action.
- Execute action through the LeRobot robot interface.
- Record local communication and execution status.

Server responsibilities:

- Receive observation.
- Run ACT / SmolVLA / Pi0 or other policy inference.
- Return action.
- Record inference time, input FPS, action FPS, latency, and events.
- Publish latest state to WebUI.

### `remote_teleoperation`

Leader and follower arms can live on different hosts on the same LAN or Tailscale virtual LAN. TCP transports leader actions to the follower side. Later, this should support dataset recording in LeRobot dataset format.

Data flow:

```text
Leader arm -> TCP action stream -> follower host -> SO-101 follower action
```

Future recording flow:

```text
Leader arm + cameras -> remote teleop server -> follower arm + dataset recorder
```

## Protocol Design

Message types:

- `OBSERVATION`
- `ACTION`
- `HEARTBEAT`
- `RESET`
- `STOP`
- `ERROR`
- `ACK`

Use a length-prefixed stream:

```text
[4-byte message length][message payload]
```

MVP payloads may use JPEG + JSON/base64 for debugging. The preferred first real version is TCP + msgpack + JPEG bytes. gRPC, ZMQ, or WebRTC should stay later-stage options.

Observation shape:

```text
Observation = {
    images,
    joint_positions,
    joint_velocities,
    gripper_state,
    timestamp,
    episode_id,
    frame_id
}
```

Action shape:

```text
Action = {
    shoulder_pan.pos,
    shoulder_lift.pos,
    elbow_flex.pos,
    wrist_flex.pos,
    wrist_roll.pos,
    gripper.pos
}
```

## Optimization

Server-side operation should eventually include a WebUI. The WebUI should show camera/image streams, joint angles, and runtime state. A useful reference is LeRobot's dataset visualization web experience, but this project should adapt the idea for live server-side experiment monitoring rather than dataset browsing.

First WebUI target: Gradio. It is fast enough for v0.1 and useful for images, values, logs, and simple plots. Later, a more formal stack can move to FastAPI + WebSocket + React.

Suggested WebUI layout:

```text
Experiment Header: mode / model / robot / status / runtime
Camera Views: top / side / wrist
Robot State: joint angle bars and gripper state
Action Output: model target action and current executed action
Network Metrics: RTT / latency / FPS / timeout and reconnect counts
Logs / Events: recent messages and error state
Safety: timeout, hold-last-action, emergency stop state
```

Open questions for planning:

- Which image streams should be displayed: robot-side camera frames, model observations, or saved run artifacts?
- Which joint-angle source should be shown: LeRobot robot state, action outputs, or both?
- Should WebUI be read-only monitoring first, or include controls later?
- Should WebUI be served by the policy server process or by a separate lightweight process?
- Should WebUI include an emergency stop button in the first implementation, or should emergency stop begin as keyboard/client-side only?
- Should WebUI refresh pull from a shared in-memory `ServerState`, an event queue, or a metrics recorder tail?

## Metrics And Run Artifacts

Each run should produce a run directory such as:

```text
runs/<timestamp>_<mode>_<task>/
  config.yaml
  metrics.csv
  events.log
  summary.json
  actions.jsonl
  images/
  videos/
```

Metrics should include:

- timestamp
- frame_id
- client capture time
- network send/return timing
- server receive time
- server inference time
- client execute time
- round trip time
- observation FPS
- action FPS
- image size
- timeout count
- reconnect count

Summary should include experiment name, mode, model, robot, duration, average/max RTT, average inference time, timeout count, and success flag when known.

## Safety Requirements

Remote robot control needs safety mechanisms from the beginning:

- Timeout stop.
- Hold last action only for a bounded short interval.
- Joint limit checks.
- Action delta limits.
- Emergency stop.
- Heartbeat.
- Safe reset before/after experiments.

Initial policy suggestion:

- If no new action for 100 ms: hold last action.
- If no new action for 500 ms: stop the robot.
- If no heartbeat for 1 s: disconnect and enter safe mode.

These numbers should be configurable and validated with hardware before being treated as final.

## Suggested Development Phases

1. **Minimum TCP communication**: config loader, protocol, TCP client/server, mock robot, mock policy, logging.
2. **Real SO-101 state**: LeRobot robot wrapper, joint state capture, action execution, safety checks, timeout.
3. **Camera images**: camera manager, JPEG encoding, multi-camera observation packaging, WebUI image display.
4. **Model inference**: policy wrapper, model loading, observation adaptation, action adaptation, inference timing.
5. **WebUI visualization**: images, joint bars, latency, inference time, logs, emergency stop.
6. **Experiment recording and comparison**: run directory, metrics, summary, saved config, local vs remote comparison scripts.

## Key Planning Questions

- What is the exact observation/action schema between LeRobot, network protocol, and policy inference?
- Which config schema should be used first: YAML + dataclasses, Pydantic, or a smaller standard-library validator?
- How much of the current LeRobot async inference path should be reused versus replaced by a custom TCP protocol for observation/action transfer?
- Should remote teleoperation and remote inference share the same TCP protocol envelope from the beginning?
- Should WebUI be part of the server process for simplicity or a separate monitor process for isolation?
- Which safety gates are mandatory before any real hardware test?
