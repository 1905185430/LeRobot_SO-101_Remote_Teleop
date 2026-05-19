# Phase 7 Research: SO-101 Local TCP Dataset Replay Baseline

**Date:** 2026-05-19
**Status:** Complete for planning

## Summary

Phase 7 should add a project-owned dataset replay client that reads one SO-101-compatible LeRobot dataset episode and sends its actions through the existing TCP teleoperation protocol. LeRobot's official replay command remains the operator preflight/reference path, while this repository owns the TCP transport, run artifacts, local replay config, and fake validation.

## External Reference

Hugging Face LeRobot docs still document episode replay as an official workflow:

- `python -m lerobot.replay` in the main real-world robot guide:
  https://huggingface.co/docs/lerobot/main/getting_started_real_world_robot
- `lerobot-replay` in the current imitation learning robot guide:
  https://huggingface.co/docs/lerobot/il_robots

Planning implication: use official replay to verify dataset/follower sanity before this project's TCP replay, but do not depend on `lerobot.replay` internal control flow. Keep the implementation behind a small dataset adapter boundary.

## Local Code Findings

- `lerobot_remote/config/schema.py` has no dataset replay section. Add one without changing the simple scalar YAML parser.
- `configs/teleop/local_so101_tcp.yaml` proves the current local follower/leader path. Phase 7 should create a replay config under `configs/replay/`.
- `TcpTeleopLeaderClient` already has socket send, ACK validation, RTT metrics, action message construction, and print behavior. Its action source is currently `leader_device.get_action()`, so dataset replay should reuse the TCP protocol behavior without requiring a physical leader.
- `TcpTeleopFollowerServer` already enforces message ordering, action key matching, first-action delta, per-frame delta limiting, value ranges, metrics, events, and ACKs. Dataset replay should keep this follower unchanged.
- `JsonlMetricsRecorder` and runtime common helpers already create run directories, metadata, copied config, metrics, events, and summary files.
- Tests already use fake leader/follower devices and fake LeRobot modules. Phase 7 should follow that style and avoid requiring SO-101 hardware, HuggingFace network access, or an installed real LeRobot package.
- Local development environment currently cannot import `lerobot`; the implementation must lazy-import LeRobot dataset APIs and keep fake tests independent of that dependency.

## Planning Decisions

- Keep the shared local replay YAML compatible with the existing follower entrypoint. Use `experiment.mode: remote_teleoperation` so `scripts/run_teleop_follower.py` can start the follower from the same config.
- Add a `dataset:` section to the platform config:
  - `path`
  - `episode`
  - `start_frame`
  - `end_frame`
  - `timing`
  - `replay_frequency`
- Use `fixed_hz` as the primary timing path and `source_timestamps` as a supported explicit mode only when source timing metadata is available.
- Implement fail-fast behavior. Missing/invalid dataset paths, dataset read failures, invalid action shape/range, ACK mismatches, TCP failures, and timing metadata gaps must abort replay and record events.
- Do not extend the YAML parser for lists or multi-episode replay in this phase.

## Implementation Shape

Recommended package additions:

- `lerobot_remote/replay/` for dataset replay data structures, LeRobot dataset adapter, fake action source, and TCP replay client.
- `lerobot_remote/runtime/dataset_replay.py` for orchestration and run artifact wiring.
- `scripts/run_dataset_replay_client.py` for the dedicated operator entrypoint.
- `configs/replay/local_so101_tcp_dataset.yaml` for the local baseline.

## Risks

- LeRobot dataset APIs may vary by installed version. Mitigation: lazy import, focused adapter, clear error messages, fake tests, and official replay preflight documentation.
- Dataset action keys may not match the current SO-101 follower action keys. Mitigation: normalize and validate before send; keep follower key validation as the final gate.
- `source_timestamps` may be unavailable or ambiguous. Mitigation: require clear metadata and fail clearly when absent.
- Per-frame delta limiting can make physical replay diverge from the dataset trajectory. Mitigation: record the event clearly and call it out in docs.

## Open Questions Deferred

- Multi-episode batch replay.
- Two-machine remote TCP replay.
- Automatic HuggingFace download/cache selection.
- Generalized `ActionSource -> Transport -> ActionSink` command architecture.
