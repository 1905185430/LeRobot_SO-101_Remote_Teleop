---
phase: 04-so-101-smolvla-runtime-integration
status: complete
created: 2026-05-11
---

# Phase 04 Pattern Map

## Files To Modify And Closest Analogs

| Target | Role | Closest Analog | Pattern To Reuse |
|--------|------|----------------|------------------|
| `so101_remote/server.py` | Server runtime orchestration | `so101_remote/dryrun.py`, `so101_remote/recorder.py`, `so101_remote/reliability.py` | Small function orchestration with recorder context and structured events |
| `so101_remote/client.py` | Robot client runtime orchestration | `so101_remote/server.py`, `so101_remote/dryrun.py` | Lazy LeRobot imports, thin `main()`, explicit startup sequence |
| `so101_remote/config.py` | Constant-based settings source | Existing constants in same file | Keep constants as single v1 config surface |
| `tests/test_minimal_async_scripts.py` | LeRobot-free runtime tests | Existing fake LeRobot modules in same file | Stub modules in `sys.modules`, fake thread/client, assert config kwargs |
| `README.md` / `docs/ENVIRONMENT.md` | Operator documentation | Current run/dry-run sections | Concrete commands and constant names, no YAML/CLI promise |

## Key Constraints

- Preserve lazy LeRobot imports.
- Preserve top-level script exports used by tests.
- Do not add plugin registry, YAML config, or broad CLI override layer.
- Use `JsonlMetricsRecorder` and `build_run_metadata()` for artifact creation.
- Use `record_exception_event()` and `run_with_retries()` for reliability hooks.
