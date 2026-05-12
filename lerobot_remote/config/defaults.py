"""Default operator-facing settings for the v1 constant-based workflow."""

from __future__ import annotations


# Server-side network settings.
HOST = "0.0.0.0"
PORT = 8080

# Robot-side network and hardware settings.
SERVER_ADDRESS = "192.168.1.151:8080"
ROBOT_PORT = "/dev/ttyACM0"
ROBOT_ID = "my_blue_follower_arm"

# Camera settings. Camera names must match the policy observation image keys.
CAMERAS = {
    "front": {
        "index_or_path": 0,
        "width": 640,
        "height": 480,
        "fps": 30,
    }
}

# Policy/model settings.
TASK = "Grasp a lego block and put it in the bin."
POLICY_TYPE = "smolvla"
PRETRAINED_NAME_OR_PATH = "HF_USER/FINETUNE_MODEL_NAME"
POLICY_DEVICE = "cuda"

# Action execution settings.
ACTIONS_PER_CHUNK = 30
CHUNK_SIZE_THRESHOLD = 0.5
AGGREGATE_FN_NAME = "weighted_average"
DEBUG_VISUALIZE_QUEUE_SIZE = False
