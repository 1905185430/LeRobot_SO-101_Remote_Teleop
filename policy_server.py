"""Minimal LeRobot async inference server entrypoint for exploration."""

from __future__ import annotations

from so101_remote.server import HOST, PORT, build_server_config, main


if __name__ == "__main__":
    raise SystemExit(main())
