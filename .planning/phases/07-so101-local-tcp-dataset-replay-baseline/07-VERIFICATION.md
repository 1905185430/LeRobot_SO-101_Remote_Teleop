# Phase 7 Verification: SO-101 Local TCP Dataset Replay Baseline

**Date:** 2026-05-20
**Status:** Automated verification passed; real SO-101 dataset/hardware replay pending operator UAT

## Commands Run

| Command | Result |
|---------|--------|
| `python3 scripts/run_dataset_replay_client.py --config configs/replay/local_so101_tcp_dataset.yaml --dry-run` | PASS |
| `python3 scripts/run_teleop_follower.py --config configs/replay/local_so101_tcp_dataset.yaml --dry-run` | PASS |
| `python3 -m unittest tests.test_config_loader tests.test_dataset_replay -v` | PASS, 22 tests during 07-01 |
| `python3 -m unittest tests.test_dataset_replay tests.test_tcp_teleop -v` | PASS, 23 tests during 07-02 |
| `python3 -m unittest discover -s tests -v` | PASS, 90 tests |
| `git diff --check` | PASS |

## Requirement Coverage

| Requirement | Evidence | Status |
|-------------|----------|--------|
| DATASET-TCP-01 | `DatasetReplayConfig`, `PlatformConfig.dataset`, `configs/replay/local_so101_tcp_dataset.yaml`, config loader tests. | Covered by automated tests |
| DATASET-TCP-02 | `DatasetReplayTcpClient`, `run_dataset_replay_client`, fake dataset TCP roundtrip test. | Covered by automated tests |
| DATASET-TCP-03 | Bundled replay config uses `127.0.0.1:9012`; docs state two-machine remote replay is deferred. | Covered by config/docs |
| DATASET-TCP-04 | Replay validates action ranges before send; existing follower tests cover key matching, first-action delta, per-frame delta limiting, and ranges. | Covered by automated tests |
| DATASET-TCP-05 | Fake runtime test asserts `metadata.json`, `events.jsonl`, `metrics.jsonl`, `metrics.csv`, `summary.md`, and `config.yaml` are created with dataset metadata. | Covered by automated tests |
| DATASET-TCP-06 | `tests/test_dataset_replay.py` uses fake dataset and fake follower; no hardware, HuggingFace network, or real LeRobot package is required. | Covered by automated tests |
| DATASET-TCP-07 | `docs/reproduction/SO101_LOCAL_TCP_DATASET_REPLAY.md`, reproduction index, and config README document prerequisites, YAML fields, startup order, validation, artifacts, and boundaries. | Covered by docs |

## Hardware UAT Still Pending

The automated suite proves the config, parser, fake dataset source, TCP protocol path, run artifacts, dry-run entrypoints, and fake follower behavior.

It does not prove:

- a real local LeRobot SO-101 dataset can be opened in the user's target LeRobot environment;
- a real SO-101 follower safely executes the replayed dataset actions;
- the selected dataset's first frame is close enough to the physical follower startup pose;
- source timestamp replay is correct for a specific real dataset;
- long-running physical replay is safe around the actual workspace.

Operator UAT should follow:

1. Run official LeRobot replay first for the selected dataset/episode/follower.
2. Run `python3 scripts/run_teleop_follower.py --config configs/replay/local_so101_tcp_dataset.yaml`.
3. Run `python3 scripts/run_dataset_replay_client.py --config configs/replay/local_so101_tcp_dataset.yaml`.
4. Inspect both run directories, especially `events.jsonl`, `metadata.json`, and `summary.md`.

## Decision Coverage

- Official LeRobot replay is documented as preflight/reference, not the TCP implementation.
- YAML uses scalar `dataset:` fields only; no multi-episode list parsing was added.
- `fixed_hz` is the default and tested timing path; `source_timestamps` fails clearly if timestamps are absent.
- Replay failures are fail-fast; no skip, clamp-to-continue, or pause/continue operator loop was added.
- Dedicated `scripts/run_dataset_replay_client.py` was added; `run_teleop_leader.py` was not overloaded.

## Verdict

Phase 7 automated verification passes. The implementation is ready for real SO-101 local TCP dataset replay UAT.
