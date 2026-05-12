"""SO-101 and SmolVLA adapter locations for LeRobot-backed runtime paths."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SO101LeRobotAdapter:
    """Concrete adapter location for the first SO-101 robot path."""

    robot_id: str
    port: str
    camera_names: tuple[str, ...]

    def describe(self) -> dict[str, object]:
        return {
            "robot_id": self.robot_id,
            "port": self.port,
            "camera_names": self.camera_names,
            "backend": "lerobot-so101",
        }

    def connect(self) -> None:
        self._raise_phase4()

    def disconnect(self) -> None:
        self._raise_phase4()

    def read_observation(self) -> dict[str, object]:
        self._raise_phase4()

    def apply_action(self, action: object) -> None:
        self._raise_phase4()

    def _raise_phase4(self) -> None:
        raise NotImplementedError("LeRobot SO-101 runtime wiring happens in Phase 4.")


@dataclass
class SmolVLAPolicyAdapter:
    """Concrete adapter location for the first SmolVLA policy path."""

    policy_type: str = "smolvla"
    pretrained_name_or_path: str = ""
    device: str = "cuda"

    def describe(self) -> dict[str, object]:
        return {
            "policy_type": self.policy_type,
            "pretrained_name_or_path": self.pretrained_name_or_path,
            "device": self.device,
            "backend": "lerobot-smolvla",
        }

    def load(self) -> None:
        self._raise_phase4()

    def infer_action(self, observation: dict[str, object]) -> object:
        self._raise_phase4()

    def _raise_phase4(self) -> None:
        raise NotImplementedError("SmolVLA runtime wiring happens in Phase 4.")
