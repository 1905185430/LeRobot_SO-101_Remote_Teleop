# Phase 7: SO-101 Local TCP Dataset Replay Baseline — Specification

**Created:** 2026-05-19
**Ambiguity score:** 0.18 (gate: <= 0.20)
**Requirements:** 7 locked

## Goal

An operator can select an existing LeRobot SO-101 dataset from YAML and replay selected episode actions through the local TCP follower path on `127.0.0.1`, producing run artifacts that prove which dataset frames were replayed and whether safety checks passed.

## Background

The repository already has config-driven TCP teleoperation for SO-101:

- local follower/server command: `python3 scripts/run_teleop_follower.py --config configs/teleop/local_so101_tcp.yaml`
- local leader/client command: `python3 scripts/run_teleop_leader.py --config configs/teleop/local_so101_tcp.yaml`
- remote follower/client variants under `configs/teleop/remote_so101_tcp.yaml`
- TCP protocol, action normalization, first-frame safety, per-frame delta limiting, run artifacts, metrics, events, summaries, and WebUI state under `lerobot_remote/`
- reproduction docs for SO-101 local TCP and SO-101 wireless TCP teleoperation

What does not exist yet is a dataset-driven replay role. Current TCP teleoperation reads a live leader device and streams actions to the follower. The next experiment needs to replay actions from an existing LeRobot SO-101 dataset instead. Dataset acquisition is not the core problem: the operator may create a dataset locally with LeRobot commands or download one from HuggingFace beforehand. The phase must first prove the local TCP replay path before moving to a two-machine remote TCP replay phase.

## Requirements

1. **YAML dataset selection**: The local replay configuration selects an existing LeRobot dataset by local path.
   - Current: `PlatformConfig` has experiment, robot, teleop, model, camera, network, runtime, safety, webui, and logging sections, but no dataset replay section.
   - Target: A config file can name the dataset path, episode selection, replay frequency or source timing mode, and output run directory for local dataset replay.
   - Acceptance: Loading the bundled local dataset replay config exposes the dataset path and replay controls; missing dataset path is rejected with a clear config error.

2. **Dataset action replay role**: Runtime can stream dataset episode actions through TCP without reading a physical leader arm.
   - Current: `TcpTeleopLeaderClient` gets actions from `leader_device.get_action()`, so replay requires a live leader device.
   - Target: A dataset replay client reads selected frames from a LeRobot SO-101 dataset and sends ACTION messages compatible with the existing TCP follower server.
   - Acceptance: A fake dataset with known SO-101 actions can be replayed to a fake follower server over TCP, and the follower receives the expected ordered actions.

3. **Local TCP baseline only**: Phase 7 uses one machine and localhost TCP.
   - Current: Local and remote SO-101 TCP configs both exist, but dataset replay has not been scoped.
   - Target: The first replay config and docs use `127.0.0.1` and a local follower/server; two-machine remote TCP replay remains explicitly out of scope.
   - Acceptance: Bundled replay docs and default config use `127.0.0.1`; no acceptance criterion requires two physical machines.

4. **Safety preservation**: Dataset replay keeps existing SO-101 TCP teleoperation safety behavior.
   - Current: Live leader TCP teleoperation validates action keys, action range, first-action delta, and per-frame delta limits.
   - Target: Dataset-sourced actions go through equivalent normalization and safety enforcement before reaching the follower, without weakening configured limits.
   - Acceptance: Tests prove invalid action keys/ranges fail, first-action delta remains enforced by the follower server, and action delta limiting still applies during replay.

5. **Replay run artifacts**: Replay outputs identify the exact dataset replayed.
   - Current: Teleoperation run directories record role, resolved config, endpoint, metrics, events, and summary, but no dataset path or episode metadata.
   - Target: Replay run artifacts include dataset path, selected episode ids or ranges, frame count, replay timing mode/frequency, TCP endpoint, safety settings, and skipped/failed frame counts.
   - Acceptance: A replay dry-run/fake-run creates `metadata.json`, `events.jsonl`, metrics output, copied config, and `summary.md` containing dataset replay metadata.

6. **Hardware-free validation path**: Replay parsing and TCP behavior are testable without SO-101 hardware or a real LeRobot dataset.
   - Current: Unit tests cover fake TCP teleoperation and config loading, but not dataset replay.
   - Target: Tests can use a small fake dataset fixture and fake follower to validate config parsing, action extraction, TCP ordering, metrics/events, and summary generation.
   - Acceptance: `python3 -m unittest discover -s tests -v` passes with dataset replay tests included, without requiring hardware or HuggingFace network access.

7. **Operator documentation**: Documentation separates dataset source, local replay, and future remote replay.
   - Current: Reproduction docs explain local SO-101 TCP teleoperation and wireless SO-101 TCP teleoperation, but not dataset replay.
   - Target: A reproduction or experiment doc explains prerequisites, how to point YAML at an existing dataset path, local startup order, validation commands, expected artifacts, and explicit boundaries.
   - Acceptance: Docs state that LeRobot dataset collection and HuggingFace download are operator-provided inputs for this phase, while remote two-machine replay is deferred.

## Boundaries

**In scope:**

- A local dataset replay phase for SO-101 only.
- YAML-selectable local LeRobot dataset path.
- Episode/frame selection and replay timing controls sufficient for local experiments.
- Dataset action extraction into SO-101 six-joint action messages.
- Local TCP replay client behavior compatible with the existing follower server.
- Existing safety checks and run artifacts applied to dataset replay.
- Fake dataset/fake follower tests that do not require hardware or network access.
- Operator documentation for local dataset replay.

**Out of scope:**

- Collecting LeRobot datasets — the operator can use LeRobot commands separately.
- Automatic HuggingFace dataset download — datasets may be downloaded beforehand and referenced by path.
- Two-machine remote TCP dataset replay — deferred to the next phase after local replay is proven.
- VLA inference, policy evaluation, or model training on the replayed dataset — separate experiment class.
- Retargeting arbitrary non-SO-101 datasets — this phase expects SO-101-compatible action dimensions/keys.
- Camera/video replay to robot hardware — this phase replays robot action trajectories; observations/images may be inspected for metadata but are not sent as robot commands.
- Weakening or bypassing teleoperation safety limits to force a dataset to replay.

## Constraints

- The implementation must preserve validated SO-101 TCP teleoperation commands and safety semantics.
- Runtime artifacts remain under configured `experiment.save_dir` and must keep config copies for reproducibility.
- Unit and fake integration tests must not require SO-101 hardware, HuggingFace network access, or a real downloaded dataset.
- YAML parsing currently supports nested mappings and scalar values only; any config shape must respect that limitation unless the phase explicitly extends the parser with tests.
- The first default config must use `127.0.0.1` and local ports to keep the baseline one-machine.

## Acceptance Criteria

- [ ] A Phase 7 YAML config can select a local LeRobot dataset path and local TCP endpoint.
- [ ] Missing or invalid dataset path fails before sending any command to the follower.
- [ ] A dataset replay client can send ordered SO-101 action frames to the existing TCP follower server protocol.
- [ ] Replay does not require a physical leader arm.
- [ ] Replay preserves action key validation, action range checks, first-action delta checks, and per-frame delta limiting.
- [ ] Replay run artifacts include dataset path, episode selection, frame count, replay timing, endpoint, safety settings, and replay error/skip counts.
- [ ] Hardware-free tests cover config parsing, fake dataset replay, TCP frame ordering, metrics/events, and summary generation.
- [ ] Documentation explains local dataset replay and explicitly defers dataset collection, automatic HuggingFace download, and remote two-machine replay.
- [ ] `python3 -m unittest discover -s tests -v` passes.

## Ambiguity Report

| Dimension          | Score | Min  | Status | Notes |
|--------------------|-------|------|--------|-------|
| Goal Clarity       | 0.90  | 0.75 | met    | Goal changed from dataset collection to replaying an existing dataset through TCP. |
| Boundary Clarity   | 0.82  | 0.70 | met    | Local TCP only; dataset collection, automatic HF download, and remote replay are out of scope. |
| Constraint Clarity | 0.74  | 0.65 | met    | YAML path selection, existing safety, local endpoint, fake tests, and parser constraints are explicit. |
| Acceptance Criteria| 0.78  | 0.70 | met    | Pass/fail checks cover config, replay, safety, artifacts, docs, and tests. |
| **Ambiguity**      | 0.18  | <=0.20 | met | Ready for discuss/plan. |

Status: met = meets minimum; below = planner treats as assumption

## Interview Log

| Round | Perspective | Question summary | Decision locked |
|-------|-------------|------------------|-----------------|
| 1 | Researcher | What is the target dataset output? | Initial assumption was LeRobot dataset, then corrected: dataset acquisition is not key; replaying an existing dataset over TCP is key. |
| 1 | Simplifier | What is the local MVP? | First implementation should be a local TCP baseline before remote TCP. |
| 1 | Boundary Keeper | What should YAML control? | YAML must let the operator select the dataset path. |
| 2 | Boundary Keeper | Is HuggingFace download part of this phase? | No. The operator may download or collect data separately; Phase 7 consumes a local dataset path. |
| 2 | Failure Analyst | What would make the phase wrong? | Building dataset collection instead of dataset replay, weakening safety limits, or requiring remote two-machine hardware in the local baseline. |

---

*Phase: 07-so101-local-tcp-dataset-replay-baseline*
*Spec created: 2026-05-19*
*Next step: $gsd-discuss-phase 7 — implementation decisions for how to build the locked requirements above*
