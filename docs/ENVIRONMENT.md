# Environment Setup

This guide prepares the two-machine LAN setup used by the v1 SO-101 + SmolVLA remote inference workflow. The current v1 configuration path is still constant-based: edit the operator-facing constants in `policy_server.py` and `robot_client.py` before running real hardware.

## GPU Server Setup

Use this machine for the LeRobot async inference policy server and model execution.

### Python And LeRobot

1. Create and activate the Python environment you use for LeRobot.
2. Install LeRobot with async inference support by following the official LeRobot instructions for your version.
3. Check that LeRobot imports in that environment:

```bash
python3 -c "import lerobot; print('lerobot import ok')"
```

### CUDA And PyTorch

Check that PyTorch can see CUDA before starting a real SmolVLA server:

```bash
python3 -c "import torch; print(torch.cuda.is_available())"
```

Expected result for GPU inference is `True`. If it prints `False`, fix CUDA, drivers, PyTorch, or environment activation before collecting communication metrics.

### Model Access

Set the SmolVLA model path in the robot/client configuration to the model you want LeRobot to load:

- `PRETRAINED_NAME_OR_PATH`
- `POLICY_TYPE`
- `POLICY_DEVICE`

If the model is hosted on HuggingFace, make sure the server environment has the required HuggingFace access before a real run.

### Server Constants

Edit these constants before running the server:

- `HOST`: defaults to `0.0.0.0`, which binds all network interfaces.
- `PORT`: defaults to `8080`.

Binding `HOST = "0.0.0.0"` is convenient on a trusted LAN, but the server should be firewalled or bound to a narrower interface on untrusted networks.

### Policy Server Preflight

Run:

```bash
python3 policy_server.py
```

Before connecting the robot-side client, confirm:

- The process starts without a LeRobot import error.
- The configured port is not already in use.
- The robot-side computer can reach the server IP and port on the LAN.

## Robot-Side Computer Setup

Use this machine for the SO-101 follower arm, cameras, and LeRobot async inference robot client.

### Python And LeRobot

Install LeRobot in the robot-side environment as well:

```bash
python3 -c "import lerobot; print('lerobot import ok')"
```

### SO-101 Serial Port

Check available serial devices:

```bash
ls /dev/ttyACM*
```

Check group membership if the serial device is permission denied:

```bash
groups
```

If needed, add the user to the serial device group used by your Linux distribution, then log out and back in.

### Robot And Camera Constants

Edit these constants before running the client:

- `SERVER_ADDRESS`: server address in `IP:PORT` form.
- `ROBOT_PORT`: SO-101 serial device path, such as `/dev/ttyACM0`.
- `ROBOT_ID`: follower calibration id.
- `CAMERAS`: camera names, index/path, width, height, and fps.
- `TASK`: text instruction sent to the VLA policy.
- `POLICY_TYPE`: defaults to `smolvla`.
- `PRETRAINED_NAME_OR_PATH`: HuggingFace or local model path.
- `POLICY_DEVICE`: defaults to `cuda`.
- `ACTIONS_PER_CHUNK`: number of actions requested per chunk.
- `CHUNK_SIZE_THRESHOLD`: queue threshold that triggers another inference request.
- `AGGREGATE_FN_NAME`: overlapping action chunk aggregation function.
- `DEBUG_VISUALIZE_QUEUE_SIZE`: whether to visualize action queue size on exit.

Camera keys in `CAMERAS` must match the observation image keys expected by the trained or downloaded policy.

### Robot Client Preflight

Run:

```bash
python3 robot_client.py
```

Before a physical run, confirm:

- The serial port points at the SO-101 follower arm.
- `ROBOT_ID` matches the follower calibration id.
- Cameras open at the configured index or path.
- `SERVER_ADDRESS` points at the GPU server.

## LAN Communication Checks

The v1 target topology is a GPU server and a robot-side computer on the same local network.

On the robot-side computer, check basic reachability:

```bash
ping <server-ip>
```

Check the configured server endpoint:

```bash
python3 - <<'PY'
import socket
host = "<server-ip>"
port = 8080
with socket.create_connection((host, port), timeout=3):
    print("connection ok")
PY
```

If the connection fails:

- Confirm `HOST` and `PORT` on the server.
- Confirm `SERVER_ADDRESS` on the robot-side client.
- Check firewall rules on the server.
- Confirm both machines are on the expected LAN or routed subnet.

## Time Synchronization

Latency and RTT interpretation is more trustworthy when the server and robot-side computer have synchronized clocks.

Recommended checks:

- Enable NTP or chrony on both machines.
- Record whether clocks are synchronized before experiments.
- Treat one-way latency carefully if clocks are not synchronized.
- Prefer RTT or same-machine interval metrics when clock sync is unknown.

## Dry-Run / Mock Setup

Dry-run support is part of the v1 roadmap. Once implemented, use it to validate runtime wiring, run directories, metric files, and summaries without SO-101 hardware or a real model.

Dry-run does not validate:

- Real SO-101 serial control.
- Real camera frames.
- Real SmolVLA loading or inference.
- Physical safety behavior.

It is only for checking the code path and metrics plumbing before a hardware session.

## Common Failures

### LeRobot Import Failure

Symptom: `LeRobot async inference is not available`.

Fix:

- Activate the correct Python environment.
- Install LeRobot with async inference support.
- Re-run `python3 -c "import lerobot"`.

### CUDA Unavailable

Symptom: `torch.cuda.is_available()` prints `False` on the server.

Fix:

- Check GPU driver and CUDA runtime.
- Treat this as a CUDA unavailable environment until the check prints `True`.
- Install a PyTorch build matching your CUDA version.
- Confirm the process is running in the environment where PyTorch is installed.

### Invalid Model Path

Symptom: model loading fails or HuggingFace access is denied.

Fix:

- Check `PRETRAINED_NAME_OR_PATH`.
- Verify HuggingFace credentials if the model is private.
- Confirm the model matches `POLICY_TYPE`.

### Camera Index Mismatch

Symptom: camera cannot open or observations do not match policy keys.

Fix:

- Check `CAMERAS`.
- Confirm the camera index or path.
- Confirm camera names match policy observation keys.

### Serial Port Permission Failure

Symptom: SO-101 device cannot open.

Fix:

- Check `ROBOT_PORT`.
- Check `ls /dev/ttyACM*`.
- Check user groups with `groups`.
- Reconnect the device or reboot if the serial device is stale.

### Server Connection Failure

Symptom: robot client cannot connect to the policy server.

Fix:

- Treat this as a server connection issue until the robot-side computer can reach the configured endpoint.
- Confirm `python3 policy_server.py` is running.
- Confirm `SERVER_ADDRESS` uses the server LAN IP and `PORT`.
- Check firewall rules and routing.

### Metrics Output Confusion

Symptom: latency, RTT, or queue metrics are missing or hard to interpret.

Fix:

- Confirm the current phase actually records the metric you expect.
- Check whether LeRobot exposes the required timing or queue signal.
- Check time synchronization before trusting one-way latency.
- Prefer structured run artifacts once metrics and run directories are implemented.
