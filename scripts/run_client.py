#!/usr/bin/env python3
"""Config-driven client entrypoint for remote modes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from so101_remote.config_loader import load_config
from so101_remote.config_schema import ConfigError
from so101_remote.runtime import configured_runtime_summary, run_configured_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to a platform YAML/JSON config.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config and print resolved client settings without touching hardware.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    if config.mode not in {"remote_inference", "remote_teleoperation", "debug_mock"}:
        print(f"Config mode '{config.mode}' is not a client mode.", file=sys.stderr)
        return 2

    print(json.dumps(configured_runtime_summary("client", config), indent=2, sort_keys=True))
    if args.dry_run:
        return 0

    return run_configured_client(config)


if __name__ == "__main__":
    raise SystemExit(main())
