---
last_mapped: 2026-05-11
last_mapped_commit: 2dd7d89
focus: quality
---

# Conventions

## Code Style

- Python code uses `from __future__ import annotations`.
- Functions and variables use snake case.
- Constants use upper snake case.
- Classes use PascalCase.
- Public functions generally have short docstrings.
- The current main scripts are intentionally thin wrappers around LeRobot APIs.

## Configuration Style

- Main-path configuration is constant-based and edited directly in `policy_server.py` and `robot_client.py`.
- The README explicitly tells users to edit constants before running scripts.
- Legacy CLIs use `argparse` flags instead of hard-coded operator settings.
- Empty `configs/` directories exist, but there is no active config loading layer.

## Dependency Handling

- Optional or environment-specific LeRobot imports are delayed until runtime.
- Main scripts raise user-facing `RuntimeError` messages when LeRobot is unavailable.
- `robot_client.py` tries multiple SO-101 follower config module paths to preserve compatibility across LeRobot versions.
- Tests use fake modules in `sys.modules` instead of requiring LeRobot to be installed.

## Error Handling

- `ProtocolError` is used for invalid legacy UDP payloads.
- Legacy loops catch `KeyboardInterrupt` and return `0`.
- Legacy CLI `main()` functions log exceptions and return `1`.
- Legacy cleanup uses broad `Exception` catches only for best-effort disconnect cleanup.
- Main `robot_client.py` stops and joins on `KeyboardInterrupt`, but normal cleanup for non-interrupt failure paths is minimal.

## Runtime Loop Patterns

- Legacy loops use a fixed `period_s = 1.0 / hz`.
- Legacy loops advance `next_tick` and sleep for remaining time.
- If the loop falls behind, `next_tick` is reset to `time.perf_counter()`.
- Legacy sockets are set to non-blocking mode.

## Protocol Patterns

- Legacy JSON payloads use compact separators and ASCII encoding.
- Legacy messages include explicit `msg_type` fields.
- Legacy action values are normalized to floats.
- Legacy action dictionaries must include all expected SO-101 joint keys.
- Legacy sequence numbers must be non-negative integers and monotonic on the follower.

## Logging

- `legacy/logging_utils.py` defines a shared log format.
- Legacy leader logs RTT summaries.
- Legacy follower logs latency summaries, timeout state, stream recovery, invalid packets, and clock skew warnings.
- Main LeRobot scripts rely mostly on upstream LeRobot behavior and minimal local messages.

## Comments And Language

- Current main scripts contain bilingual English and Chinese comments/docstrings.
- Legacy protocol contains extensive Chinese explanatory comments.
- Tests use English names and assertions.

## Testing Conventions

- Tests are standard-library `unittest`, not `pytest`.
- Hardware and LeRobot are mocked or stubbed.
- Socket behavior is tested with localhost UDP socket pairs.
- Timing-sensitive behavior is tested by injecting timestamps where possible.
