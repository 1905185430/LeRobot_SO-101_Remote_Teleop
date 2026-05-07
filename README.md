# LeRobot SO-101 Remote Teleop

Minimal UDP bridge for running an SO-101 leader arm and follower arm on different computers with LeRobot.

The bridge preserves LeRobot's native SO-101 action format: joint-name dictionaries such as
`{"shoulder_pan.pos": ..., "gripper.pos": ...}`.

It also supports ping-like latency monitoring:
- the follower immediately sends a UDP ACK for every valid action packet
- the leader measures round-trip time (RTT) with its own monotonic clock
- this RTT output does not depend on the two machines having synchronized system clocks

## Files

- `leader_sender.py`: reads `SO101Leader.get_action()` and streams validated JSON packets over UDP
- `follower_receiver.py`: receives packets, holds the last valid target on timeout, and forwards to `SO101Follower.send_action()`
- `protocol.py`: wire schema, encoding, decoding, and validation
- `logging_utils.py`: shared logging setup

The follower terminal also prints periodic link timing stats:
- `latest`: most recent one-way packet age derived from `sent_at_ns`
- `avg` / `max`: running averages over all received packets
- `stream_age`: time since the last valid packet arrived, based on the follower's monotonic clock

If the two machines are not time-synchronized, the follower will detect negative wall-clock deltas and switch the terminal output to `Clock skew detected ... stream_age=...` instead of showing misleading negative latency numbers. In that case, `stream_age` is the reliable freshness signal, and syncing both machines with NTP or `chrony` will restore meaningful one-way latency stats.

For the most stable delay metric, watch the leader terminal RTT logs. They behave more like `ping`:
- `latest`: latest measured round-trip time
- `avg` / `min` / `max`: running RTT statistics
- `in_flight`: action packets that have been sent but not yet acknowledged

## Wire Format

Leader packets are JSON objects with an `action` dictionary:

```json
{
  "msg_type": "action_v1",
  "seq": 12,
  "sent_at_ns": 1710000000000000000,
  "leader_id": "so_leader",
  "action": {
    "shoulder_pan.pos": 0.0,
    "shoulder_lift.pos": 1.2,
    "elbow_flex.pos": 2.3,
    "wrist_flex.pos": 0.4,
    "wrist_roll.pos": 1.1,
    "gripper.pos": 0.0
  }
}
```

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
  --timeout-ms 200 \
  --latency-log-interval 1.0
```

Then start the leader machine:

```bash
python3 leader_sender.py \
  --leader-port /dev/ttyACM0 \
  --leader-id leader_arm \
  --follower-ip 192.168.1.100 \
  --udp-port 5005 \
  --hz 50 \
  --rtt-log-interval 1.0
```

## Test

This project uses the standard library `unittest` runner so it works even if `pytest` is not installed:

```bash
python3 -m unittest discover -s tests -v
```
