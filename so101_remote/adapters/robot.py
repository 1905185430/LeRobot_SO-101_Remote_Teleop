"""Robot adapter boundary for future hardware integrations."""

from __future__ import annotations

from typing import Protocol


class RobotAdapter(Protocol):
    """Minimal robot adapter surface reserved for later phases."""

    robot_id: str
