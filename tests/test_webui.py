from __future__ import annotations

from dataclasses import replace
import sys
import unittest
from unittest import mock

from so101_remote.config_loader import load_config
from so101_remote.webui import (
    DashboardState,
    launch_dashboard,
    render_dashboard_snapshot,
    render_images_html,
)


class WebUITests(unittest.TestCase):
    def test_dashboard_state_updates_observation_action_and_latency(self) -> None:
        config = load_config("configs/debug_mock_robot.yaml")
        state = DashboardState.from_config(config, "mock-server")

        state.update_connection("client connected")
        state.update_observation(
            {
                "frame_id": 7,
                "joint_positions": {"shoulder_pan.pos": 0.25},
                "images": {"front": "abc123"},
            }
        )
        state.update_action({"frame_id": 7, "action": {"shoulder_pan.pos": 0.3}})
        state.update_latency(12.5, inference_ms=3.0)

        snapshot = state.snapshot()
        self.assertEqual(snapshot["connection_status"], "client connected")
        self.assertEqual(snapshot["latest_joint_states"], {"shoulder_pan.pos": 0.25})
        self.assertEqual(snapshot["latest_action"], {"shoulder_pan.pos": 0.3})
        self.assertEqual(snapshot["latest_latency_ms"], 12.5)
        self.assertEqual(snapshot["latest_inference_ms"], 3.0)

    def test_render_dashboard_snapshot(self) -> None:
        config = load_config("configs/debug_mock_robot.yaml")
        state = DashboardState.from_config(config, "mock-server")
        state.update_observation({"images": {"front": "abc123"}})

        status, images, joints, action, metrics, logs = render_dashboard_snapshot(state)

        self.assertEqual(status["mode"], "debug_mock")
        self.assertIn("front", images)
        self.assertEqual(joints, {})
        self.assertEqual(action, {})
        self.assertEqual(metrics["image_count"], 1)
        self.assertIn("observation", logs)

    def test_render_images_html_handles_empty_and_base64_payloads(self) -> None:
        self.assertIn("No images", render_images_html({}))
        rendered = render_images_html({"front": "abc123"})
        self.assertIn("data:image/jpeg;base64,abc123", rendered)

    def test_launch_dashboard_disabled_returns_none(self) -> None:
        config = load_config("configs/debug_mock_robot.yaml")
        state = DashboardState.from_config(config, "mock-server")

        self.assertIsNone(launch_dashboard(config, state))

    def test_launch_dashboard_missing_gradio_returns_none(self) -> None:
        config = load_config("configs/debug_mock_robot.yaml")
        config = replace(config, webui=replace(config.webui, enabled=True))
        state = DashboardState.from_config(config, "mock-server")

        with mock.patch.dict(sys.modules, {"gradio": None}):
            self.assertIsNone(launch_dashboard(config, state))

        self.assertTrue(any("gradio is not installed" in event for event in state.snapshot()["events"]))


if __name__ == "__main__":
    unittest.main()
