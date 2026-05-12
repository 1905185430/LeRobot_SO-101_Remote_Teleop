"""Minimal LeRobot async inference client entrypoint for SO-101 exploration."""

from __future__ import annotations

from lerobot_remote import client as _client
from lerobot_remote.client import (
    ACTIONS_PER_CHUNK,
    AGGREGATE_FN_NAME,
    CAMERAS,
    CHUNK_SIZE_THRESHOLD,
    DEBUG_VISUALIZE_QUEUE_SIZE,
    POLICY_DEVICE,
    POLICY_TYPE,
    PRETRAINED_NAME_OR_PATH,
    ROBOT_ID,
    ROBOT_PORT,
    SERVER_ADDRESS,
    TASK,
    build_camera_configs,
    build_client_metadata,
    build_client_config,
    build_robot_config,
    client_settings,
    main,
)

threading = _client.threading


if __name__ == "__main__":
    raise SystemExit(main())
