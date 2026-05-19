# Phase 7: SO-101 Local TCP Dataset Replay Baseline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-19
**Phase:** 7-SO-101 Local TCP Dataset Replay Baseline
**Areas discussed:** Dataset reading interface, YAML configuration shape, Replay timing, Safety failure behavior, Script entry and operator flow

---

## Dataset Reading Interface

| Option | Description | Selected |
|--------|-------------|----------|
| Official replay as reference/preflight, project implements TCP replay | Require official `python -m lerobot.replay` as a sanity check, then implement a project-owned TCP replay client using LeRobot dataset reading capability. | ✓ |
| Wrap LeRobot replay internals | Reuse internal `lerobot.replay` episode/action traversal and replace only robot execution with TCP send. | |
| Only call official replay | Document official replay only, with no project-owned TCP replay. | |

**User's choice:** Official replay as reference/preflight, project implements TCP replay.
**Notes:** User highlighted that LeRobot already has a replay command and asked whether wireless operation should be developed on top of LeRobot's existing project format. Decision: keep LeRobot as the baseline and build the project's remote TCP layer around it rather than replacing LeRobot.

---

## YAML Configuration Shape

| Option | Description | Selected |
|--------|-------------|----------|
| New scalar `dataset:` section | Use `dataset.path`, `episode`, `start_frame`, `end_frame`, `timing`, and `replay_frequency`. Compatible with current YAML parser. | ✓ |
| Scalar range strings | Use fields such as `episodes: "0,1,2"` and `frame_range: "0:-1"` to express more without YAML lists. | |
| Extend YAML parser for lists | Add list support to express multiple episodes natively. | |

**User's choice:** New scalar `dataset:` section.
**Notes:** Phase 7 should support single-episode local replay first and avoid parser expansion.

---

## Replay Timing

| Option | Description | Selected |
|--------|-------------|----------|
| `fixed_hz` default only | Use a configured replay frequency as the primary timing model. | |
| `source_timestamps` default | Replay according to dataset timestamps/fps. | |
| Support both, default `fixed_hz` | Implement `fixed_hz` as primary acceptance path and support `source_timestamps` only when dataset timing metadata is clear. | ✓ |

**User's choice:** Support both, default `fixed_hz`.
**Notes:** `source_timestamps` must fail clearly when timing metadata is unavailable; no silent fallback.

---

## Safety Failure Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Fail fast / abort episode | Abort on invalid actions, safety failures, ACK mismatch, timeouts, connection errors, or dataset read errors. | ✓ |
| Skip bad frame | Skip invalid frames and continue replay. | |
| Clamp and continue | Clamp values to safety limits and continue replay. | |
| Pause for operator | Pause on safety/connection failures and wait for user input. | |

**User's choice:** Fail fast / abort episode.
**Notes:** Phase 7 must not hide dataset/calibration/safety problems by continuing through bad frames.

---

## Script Entry And Operator Flow

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated replay client script | Add `scripts/run_dataset_replay_client.py` and keep follower/server on `scripts/run_teleop_follower.py`. | ✓ |
| Reuse `run_teleop_leader.py` | Use config branching to source actions from dataset instead of a physical leader. | |
| Add generalized action client script | Introduce `run_action_client.py` for future leader/dataset/policy sources. | |

**User's choice:** Dedicated replay client script.
**Notes:** Avoid overloading the live leader terminology. Generalized action-source architecture is deferred.

---

## the agent's Discretion

- Exact module names and package placement are left to planning, as long as the LeRobot-compatible TCP replay boundary is preserved.
- Fake dataset fixture format is left to planning.

## Deferred Ideas

- Multi-episode batch replay.
- Remote two-machine TCP dataset replay.
- Interactive pause/continue on safety failure.
- Generalized `ActionSource -> Transport -> ActionSink` command/API.
- Automatic HuggingFace dataset download.
