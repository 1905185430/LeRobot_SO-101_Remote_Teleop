#!/usr/bin/env python3
"""Config-driven local inference entrypoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from so101_remote.config_loader import load_config
from so101_remote.config_schema import ConfigError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to a platform YAML/JSON config.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config and print resolved local settings without touching hardware.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    if config.mode not in {"local_inference", "debug_mock"}:
        print(f"Config mode '{config.mode}' is not a local mode.", file=sys.stderr)
        return 2

    print(json.dumps({"role": "local", "config": config.summary()}, indent=2, sort_keys=True))
    if args.dry_run:
        return 0

    raise RuntimeError("Config-driven local runtime is not implemented yet; use --dry-run.")


if __name__ == "__main__":
    raise SystemExit(main())
