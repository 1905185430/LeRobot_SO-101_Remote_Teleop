from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from so101_remote.dryrun import FakePolicyAdapter, FakeRobotAdapter, run_dry_run


class DryRunTests(unittest.TestCase):
    def test_fake_robot_and_policy_do_not_touch_hardware(self) -> None:
        robot = FakeRobotAdapter()
        policy = FakePolicyAdapter()

        robot.connect()
        policy.load()
        observation = robot.read_observation()
        action = policy.infer_action(observation)
        robot.apply_action(action)
        robot.disconnect()

        self.assertEqual(observation["source"], "dry-run")
        self.assertEqual(action["command"], "hold-position")
        self.assertEqual(robot.observations_read, 1)
        self.assertEqual(robot.actions_applied, 1)
        self.assertFalse(robot.connected)
        self.assertTrue(policy.loaded)

    def test_run_dry_run_writes_artifact_set(self) -> None:
        with TemporaryDirectory() as tmpdir:
            run_dir = run_dry_run(tmpdir, iterations=3)

            self.assertEqual(run_dir.parent, Path(tmpdir))
            self.assertTrue((run_dir / "metadata.json").exists())
            self.assertTrue((run_dir / "metrics.jsonl").exists())
            self.assertTrue((run_dir / "events.jsonl").exists())
            self.assertTrue((run_dir / "metrics.csv").exists())
            self.assertTrue((run_dir / "summary.md").exists())

            metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
            metrics = (run_dir / "metrics.jsonl").read_text(encoding="utf-8")
            summary = (run_dir / "summary.md").read_text(encoding="utf-8")

            self.assertEqual(metadata["role"], "dry-run")
            self.assertFalse(metadata["extra"]["validates_hardware"])
            self.assertIn("loop_interval_ms", metrics)
            self.assertIn("latency_ms", metrics)
            self.assertIn("queue_size", metrics)
            self.assertIn("# Run Summary", summary)


if __name__ == "__main__":
    unittest.main()
