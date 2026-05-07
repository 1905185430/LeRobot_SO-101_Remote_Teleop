# LeRobot SO-101 Remote Teleop

Minimal UDP bridge for running an SO-101 leader arm and follower arm on different computers with LeRobot.

## Files

- `leader_sender.py`: reads `SO101Leader.get_action()` and streams validated JSON packets over UDP
- `follower_receiver.py`: receives packets, holds the last valid target on timeout, and forwards to `SO101Follower.send_action()`
- `protocol.py`: wire schema, encoding, decoding, and validation
- `logging_utils.py`: shared logging setup

## Requirements

- Python 3.10+
- `lerobot` installed on both machines
- Both SO-101 arms calibrated with the same ids you pass at runtime

## Run

Start the follower machine first:

```bash
python3 follower_receiver.py \
  --follower-port /dev/ttyACM0 \
  --follower-id follower_arm \
  --bind-ip 0.0.0.0 \
  --udp-port 5005 \
  --hz 50 \
  --timeout-ms 200
```

Then start the leader machine:

```bash
python3 leader_sender.py \
  --leader-port /dev/ttyACM0 \
  --leader-id leader_arm \
  --follower-ip 192.168.1.100 \
  --udp-port 5005 \
  --hz 50
```

## Test

This project uses the standard library `unittest` runner so it works even if `pytest` is not installed:

```bash
python3 -m unittest discover -s tests -v
```
