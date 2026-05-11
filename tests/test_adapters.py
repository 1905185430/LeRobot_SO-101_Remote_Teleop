from __future__ import annotations

import sys
import unittest

from so101_remote.adapters import (
    PISeriesPolicyPlaceholder,
    SO101LeRobotAdapter,
    SmolVLAPolicyAdapter,
    UnsupportedPolicyAdapter,
    UnsupportedRobotAdapter,
)


class AdapterTests(unittest.TestCase):
    def test_adapter_imports_do_not_import_lerobot(self) -> None:
        self.assertNotIn("lerobot", sys.modules)

    def test_so101_adapter_describes_lerobot_backend(self) -> None:
        adapter = SO101LeRobotAdapter(
            robot_id="so101_follower", port="/dev/ttyACM0", camera_names=("front",)
        )

        self.assertEqual(
            adapter.describe(),
            {
                "robot_id": "so101_follower",
                "port": "/dev/ttyACM0",
                "camera_names": ("front",),
                "backend": "lerobot-so101",
            },
        )
        with self.assertRaisesRegex(NotImplementedError, "LeRobot SO-101 runtime wiring"):
            adapter.connect()

    def test_smolvla_adapter_describes_lerobot_backend(self) -> None:
        adapter = SmolVLAPolicyAdapter(
            pretrained_name_or_path="lerobot/smolvla_base", device="cuda"
        )

        self.assertEqual(adapter.describe()["backend"], "lerobot-smolvla")
        self.assertEqual(adapter.describe()["policy_type"], "smolvla")
        with self.assertRaisesRegex(NotImplementedError, "SmolVLA runtime wiring"):
            adapter.load()

    def test_unsupported_robot_adapter_raises_explicit_message(self) -> None:
        adapter = UnsupportedRobotAdapter(robot_id="future-arm")

        with self.assertRaisesRegex(NotImplementedError, "No robot backend is implemented for"):
            adapter.read_observation()

    def test_unsupported_policy_and_pi_placeholder_raise_explicit_messages(self) -> None:
        with self.assertRaisesRegex(NotImplementedError, "No policy backend is implemented for"):
            UnsupportedPolicyAdapter(policy_type="future-policy").load()

        with self.assertRaisesRegex(NotImplementedError, "PI-series policy support is a placeholder"):
            PISeriesPolicyPlaceholder().infer_action({})


if __name__ == "__main__":
    unittest.main()
