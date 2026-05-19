# Phase 7 Patterns: SO-101 Local TCP Dataset Replay Baseline

**Date:** 2026-05-19
**Status:** Complete for planning

## Existing Patterns To Follow

| Area | Existing pattern | Phase 7 use |
|------|------------------|-------------|
| Entrypoints | Thin scripts under `scripts/` parse `--config` and `--dry-run`, then call runtime functions. | Add `scripts/run_dataset_replay_client.py` with the same CLI feel. |
| Config | Typed dataclasses in `lerobot_remote/config/schema.py`; YAML stays scalar/nested mapping only. | Add `DatasetReplayConfig` and optional `PlatformConfig.dataset`. |
| Local TCP | Role-explicit follower/leader scripts use one YAML and `remote_teleoperation` mode. | Keep follower on `run_teleop_follower.py`; replay client reads dataset from same YAML. |
| Runtime artifacts | Runtime functions create run dir, metadata, copied config, recorder, dashboard state, and summary. | Create role `dataset-replay-client` with dataset metadata added. |
| TCP protocol | ACTION/ACK messages go through `send_message`/`recv_message`, frame IDs, and max packet size. | Reuse protocol behavior for dataset frames. |
| Safety | Client validates action values before send; follower validates keys, first-action delta, per-frame delta, ranges. | Dataset replay must pass through equivalent checks and leave follower unchanged. |
| Tests | Fake devices/modules verify behavior without real hardware or LeRobot. | Add fake dataset source and fake follower TCP tests. |
| Docs | Reproduction docs separate operator commands, validation, artifacts, and boundaries. | Add local dataset replay doc and link from reproduction index. |

## Files Most Likely To Change

- `lerobot_remote/config/schema.py`
- `lerobot_remote/config/__init__.py`
- `lerobot_remote/replay/__init__.py`
- `lerobot_remote/replay/dataset.py`
- `lerobot_remote/replay/client.py`
- `lerobot_remote/runtime/dataset_replay.py`
- `lerobot_remote/runtime/__init__.py`
- `scripts/run_dataset_replay_client.py`
- `configs/replay/local_so101_tcp_dataset.yaml`
- `configs/README.md`
- `docs/reproduction/SO101_LOCAL_TCP_DATASET_REPLAY.md`
- `docs/reproduction/REPRODUCTION.md`
- `tests/test_config_loader.py`
- `tests/test_dataset_replay.py`
- `tests/test_tcp_teleop.py` if shared TCP client behavior is refactored

## Design Notes

- Prefer a small focused replay package over a broad generic transport abstraction.
- Preserve the existing follower server exactly unless tests reveal a missing recorder event for delta limiting.
- Keep the dataset adapter defensive and easy to replace if LeRobot changes its dataset API.
- Keep the first bundled config local-only: `127.0.0.1`, one episode, scalar fields.
- Treat dry-run as config validation and operator visibility, not as proof that a real LeRobot dataset can be read.
