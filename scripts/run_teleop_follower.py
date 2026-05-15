#!/usr/bin/env python3
"""Role-explicit TCP teleoperation follower entrypoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lerobot_remote.config import ConfigError, load_config
from lerobot_remote.runtime import configured_runtime_summary
from lerobot_remote.runtime.teleoperation import run_tcp_teleop_follower_server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to a teleoperation YAML/JSON config.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config and print resolved follower settings without touching hardware.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    if config.mode != "remote_teleoperation":
        print(f"Config mode '{config.mode}' is not a teleoperation mode.", file=sys.stderr)
        return 2

    print(json.dumps(configured_runtime_summary("tcp-teleop-follower", config), indent=2, sort_keys=True))
    if args.dry_run:
        return 0

    return run_tcp_teleop_follower_server(config)


if __name__ == "__main__":
    raise SystemExit(main())
