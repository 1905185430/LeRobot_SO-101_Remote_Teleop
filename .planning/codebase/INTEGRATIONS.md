---
last_mapped: 2026-05-11
last_mapped_commit: 2dd7d89
focus: tech
---

# Integrations

## LeRobot

- LeRobot is the central runtime integration.
- `policy_server.py` delegates server behavior to `lerobot.async_inference.policy_server.serve`.
- `robot_client.py` delegates robot behavior to `lerobot.async_inference.robot_client.RobotClient`.
- `robot_client.py` constructs official LeRobot config objects rather than implementing robot control directly.
- `legacy/leader_sender.py` integrates with `SO101Leader` and `SO101LeaderConfig`.
- `legacy/follower_receiver.py` integrates with `SO101Follower` and `SO101FollowerConfig`.

## Hardware

- Target robot is SO-101.
- Main robot-side serial port defaults to `/dev/ttyACM0` in `robot_client.py`.
- Main robot id defaults to `my_blue_follower_arm` in `robot_client.py`.
- Legacy CLIs require `--leader-port`, `--leader-id`, `--follower-port`, and `--follower-id`.

## Cameras

- `robot_client.py` configures an OpenCV camera named `front`.
- The default camera config uses index `0`, resolution `640x480`, and `30` FPS.
- README notes that camera keys must match the image observation keys expected by the trained or downloaded model.

## Network

- `policy_server.py` binds the async inference server to `0.0.0.0:8080`.
- `robot_client.py` points at `192.168.1.10:8080` by default.
- The legacy path uses UDP port `5005` by default.
- Legacy leader sends action datagrams to `(follower_ip, udp_port)`.
- Legacy follower binds a UDP socket on `DEFAULT_BIND_IP = "0.0.0.0"` and sends acknowledgements back to packet senders.

## Model Source

- `robot_client.py` uses `POLICY_TYPE = "smolvla"`.
- `robot_client.py` uses `PRETRAINED_NAME_OR_PATH = "HF_USER/FINETUNE_MODEL_NAME"` as a placeholder for a HuggingFace model path or local model reference.
- `POLICY_DEVICE = "cuda"` assumes a CUDA-capable inference machine.

## External Services

- No database integration is present.
- No auth provider is present.
- No webhook integration is present.
- No cloud API calls are implemented directly in this repository.
- HuggingFace is implied by the model path placeholder, but access is mediated by LeRobot.

## Logs And Artifacts

- `logs/policy_server_1778310999.log` and `logs/robot_client_1778310991.log` exist as generated runtime logs.
- `map.png` exists at repo root; current code does not reference it.

## Security Notes

- The repository contains no obvious real API keys or private tokens.
- `HOST = "0.0.0.0"` exposes the server on all interfaces; this is convenient for LAN experiments but should be constrained or firewalled for untrusted networks.
- The legacy UDP protocol has validation and acknowledgements but no authentication, authorization, encryption, or replay protection.
