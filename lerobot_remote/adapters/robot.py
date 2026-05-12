"""Robot adapter boundary for hardware integrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class RobotAdapter(Protocol):
    """Minimal robot adapter surface used by runtime orchestration."""

    robot_id: str

    def connect(self) -> None:
        """Open the robot connection."""

    def disconnect(self) -> None:
        """Close the robot connection."""

    def read_observation(self) -> dict[str, object]:
        """Read one observation from the robot."""

    def apply_action(self, action: object) -> None:
        """Apply one action to the robot."""


@dataclass
class UnsupportedRobotAdapter:
    """Placeholder for future robot arm backends."""

    robot_id: str = "unsupported"

    def connect(self) -> None:
        self._raise()

    def disconnect(self) -> None:
        self._raise()

    def read_observation(self) -> dict[str, object]:
        self._raise()

    def apply_action(self, action: object) -> None:
        self._raise()

    def _raise(self) -> None:
        raise NotImplementedError(f"No robot backend is implemented for {self.robot_id}.")
