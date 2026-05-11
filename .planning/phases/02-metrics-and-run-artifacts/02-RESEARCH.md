---
phase: 02
slug: metrics-and-run-artifacts
status: complete
created: 2026-05-11
requirements: [METR-01, METR-02, METR-03, METR-04, METR-05, METR-06, METR-07, METR-08, METR-09, EXP-01, EXP-02, EXP-03, EXP-04, EXP-05]
---

# Phase 2 Research — Metrics And Run Artifacts

## RESEARCH COMPLETE

Phase 2 should build a local experiment artifact layer that is independent of real LeRobot execution. The implementation should make metric samples, events, run metadata, and summaries testable without hardware or LeRobot installed. Later runtime phases can call this layer from `so101_remote.client` or adapter code when real hooks are available.

## Current Codebase Shape

- `so101_remote/metrics.py`, `so101_remote/recorder.py`, and `so101_remote/dryrun.py` are import-safe placeholders created in Phase 1.
- `so101_remote/client.py` and `so101_remote/server.py` intentionally keep LeRobot imports lazy.
- Tests use standard-library `unittest` and fake modules in `sys.modules`; no pytest or LeRobot dependency is expected.
- `README.md` and `docs/ENVIRONMENT.md` already mention environment and metrics output confusion, but there is no run artifact contract yet.
- Legacy UDP code has timing concepts such as RTT, latency summaries, timeout/recovery, and loop pacing, but Phase 2 should not couple the new runtime package to `legacy/`.

## Metric Model Recommendations

Use small dataclasses and pure helper functions in `so101_remote.metrics`:

- `MetricSample`: numeric measurement with `name`, `value`, `unit`, `timestamp`, and optional `tags`.
- `MetricEvent`: non-numeric runtime event with `event_type`, `message`, `timestamp`, `severity`, and optional `details`.
- `MetricStats`: aggregate result with `count`, `min`, `max`, `mean`, and `p95`.
- `MetricCollector`: in-memory collector that records samples/events and exposes grouped statistics.

Metric names should be explicit strings that map to requirements:

- `latency_ms` for one-way or observed latency when timestamp signals exist.
- `rtt_ms` for RTT or RTT-like heartbeat/request-response timing.
- `jitter_ms` derived from adjacent latency or interval deltas.
- `loop_interval_ms` for control-loop intervals.
- `chunk_interval_ms` for action chunk arrival intervals.
- `queue_size` for queue state when LeRobot exposes it.

Events should use stable event types:

- `timeout`
- `disconnect`
- `retry`
- `recovery`
- `exception`

Jitter should be computed from ordered samples as absolute deltas between adjacent values or intervals. For v1 this is enough for local experiment comparison; more advanced wireless metrics can be added later.

## Recorder And Artifact Recommendations

Use `so101_remote.recorder` for filesystem ownership:

- Default run root: `logs/experiments`.
- Run directory format: `{YYYYMMDD-HHMMSS}-{role}-{short_id}`.
- Required files:
  - `metadata.json`
  - `metrics.jsonl`
  - `events.jsonl`
  - optional `metrics.csv`
  - generated `summary.md`

The recorder should be usable as a context manager and support direct calls:

- `create_run_directory(...)`
- `build_run_metadata(...)`
- `JsonlMetricsRecorder`
- `write_summary_markdown(...)`

`metadata.json` should include timestamp, role, server address or bind address when known, robot settings, policy/model settings, git commit when available, and free-form extra metadata.

JSONL is the most robust first storage format because it can append samples/events incrementally and preserve different metric schemas. CSV is useful for quick plotting, so Phase 2 can implement a simple `metrics.csv` with common columns: `timestamp,name,value,unit,tags`.

## Terminal Summary Recommendations

Terminal output should be readable and deterministic:

- Keep it text-only with one line per metric.
- Include `count`, `min`, `max`, `mean`, and `p95` where numeric data exists.
- Include event counts by event type.
- Avoid progress bars or live terminal dependencies in Phase 2.

Recommended helper: `format_terminal_summary(stats_by_metric, event_counts) -> str`.

## Markdown Summary Recommendations

`summary.md` should be lightweight and reproducible:

- Title with run id.
- Metadata table with role, created timestamp, server endpoint, robot id, model path, and git commit when present.
- Metric statistics table with count/min/max/mean/p95/unit.
- Event counts table.
- Files section listing `metadata.json`, `metrics.jsonl`, `events.jsonl`, and `metrics.csv` when present.

This can be generated from in-memory collector state during tests and from recorded JSONL files during later runtime integration.

## Implementation Boundaries

Do not implement real LeRobot hooks in Phase 2. Runtime integration belongs to later phases. Phase 2 should provide the API and artifact behavior that future code will call:

- No custom transport.
- No changes to official LeRobot async inference behavior.
- No dependency on hardware.
- No dependency on `legacy/`.
- No heavy configuration framework.

## Test Strategy

Add focused `unittest` coverage:

- `tests/test_metrics.py` for sample/event models, jitter, p95, grouping, event counts, and terminal summary formatting.
- `tests/test_recorder.py` for unique run directory creation, metadata fields, JSONL/CSV append behavior, and summary generation.
- Existing `tests/test_minimal_async_scripts.py` and `tests/test_legacy_demo.py` should continue passing.

## Validation Architecture

The phase has a testable validation surface without hardware:

- Pure metric/stat helpers are validated by deterministic unit tests.
- Recorder filesystem behavior is validated with `tempfile.TemporaryDirectory`.
- Markdown summary generation is validated by exact string/table assertions.
- Full regression validation remains `python3 -m unittest discover -s tests -v`.

## Planning Implications

Split the phase into three executable plans:

1. Implement metric sample/event models, statistics helpers, jitter derivation, event counts, and terminal formatting in `so101_remote.metrics` with `tests/test_metrics.py`.
2. Implement run directory creation, metadata, JSONL/CSV recorder behavior, and recorder tests in `so101_remote.recorder` with `tests/test_recorder.py`.
3. Implement Markdown summary generation, document the artifact contract in README/docs, and add tests that verify `summary.md` content and required files.
