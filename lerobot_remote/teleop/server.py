"""TCP teleoperation follower server."""

from __future__ import annotations

import socket
import time
from typing import Any, Mapping

from legacy.protocol import ProtocolError as LegacyProtocolError

from ..network.protocol import MSG_ACK, MSG_ACTION, ProtocolError, recv_message, send_message
from ..recording.metrics import EVENT_EXCEPTION, EVENT_RECOVERY, LATENCY_MS, MetricEvent, MetricSample
from ..recording.recorder import JsonlMetricsRecorder
from ..webui.state import DashboardState
from .actions import normalize_teleop_action
from .safety import validate_action_values
from .settings import TcpTeleopSettings


class TcpTeleopFollowerServer:
    """Receive TCP leader actions and apply them to a follower robot."""

    def __init__(
        self,
        follower_robot: Any,
        settings: TcpTeleopSettings,
        recorder: JsonlMetricsRecorder | None = None,
        state: DashboardState | None = None,
    ) -> None:
        self.follower_robot = follower_robot
        self.settings = settings
        self.recorder = recorder
        self.state = state
        self.last_frame_id: int | None = None
        self.last_action: dict[str, float] | None = None
        self.last_action_monotonic_ns: int | None = None

    def run(self, max_messages: int | None = None) -> int:
        """Run one-client follower receive loop."""
        processed = 0
        self.initialize_action_baseline()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((self.settings.host, self.settings.port))
            server_sock.listen(1)
            self._record_event(EVENT_RECOVERY, "tcp teleop follower listening")
            conn, _addr = server_sock.accept()
            with conn:
                conn.settimeout(self.settings.timeout_s)
                self._update_connection("client connected")
                while max_messages is None or processed < max_messages:
                    try:
                        message = recv_message(conn, max_size=self.settings.max_packet_size)
                    except socket.timeout:
                        self._handle_timeout()
                        continue
                    action = self.handle_action_message(message)
                    self.follower_robot.send_action(action)
                    send_message(
                        conn,
                        self.build_ack_message(message),
                        max_size=self.settings.max_packet_size,
                    )
                    processed += 1
        self._update_connection("closed")
        return 0

    def handle_action_message(self, message: Mapping[str, object]) -> dict[str, float]:
        """Validate an ACTION message and return normalized action."""
        if message.get("type") != MSG_ACTION:
            raise ProtocolError(f"Expected ACTION message, got {message.get('type')!r}.")
        frame_id = message.get("frame_id")
        if not isinstance(frame_id, int) or frame_id < 0:
            raise ProtocolError("ACTION frame_id must be a non-negative integer.")
        if self.last_frame_id is not None and frame_id <= self.last_frame_id:
            raise ProtocolError(
                f"Out-of-order or duplicate ACTION frame_id={frame_id}, last={self.last_frame_id}."
            )
        try:
            action = normalize_teleop_action(message.get("action"))
        except LegacyProtocolError as exc:
            raise ProtocolError(str(exc)) from exc

        self.validate_action_keys(action)
        self.validate_first_action_delta(action)
        limited_action = self.limit_action_delta(action)
        validate_action_values(
            limited_action,
            action_min=self.settings.action_min,
            action_max=self.settings.action_max,
        )
        self.last_frame_id = frame_id
        self.last_action = limited_action
        self.last_action_monotonic_ns = time.monotonic_ns()
        latency_ms = (time.time_ns() - int(message.get("timestamp_ns", time.time_ns()))) / 1_000_000
        if latency_ms >= 0:
            self._record_sample(LATENCY_MS, latency_ms, {"component": "tcp_teleop_follower"})
            if self.state is not None:
                self.state.update_latency(latency_ms)
        if self.state is not None:
            self.state.update_action({"type": MSG_ACTION, "frame_id": frame_id, "action": limited_action})
        return limited_action

    def initialize_action_baseline(self) -> None:
        """Use follower's current position as the first delta-limit baseline."""
        observation_reader = getattr(self.follower_robot, "get_observation", None)
        if not callable(observation_reader):
            self._record_event(
                EVENT_EXCEPTION,
                "tcp teleop follower cannot read startup position; action delta limit starts after first command",
            )
            return
        try:
            observation = observation_reader()
            self.last_action = normalize_teleop_action(
                {key: value for key, value in observation.items() if str(key).endswith(".pos")}
            )
            validate_action_values(
                self.last_action,
                action_min=self.settings.action_min,
                action_max=self.settings.action_max,
            )
        except Exception as exc:
            raise RuntimeError(
                "Failed to read follower startup position for TCP teleop safety. "
                "Check follower connection/calibration before enabling teleoperation."
            ) from exc
        self._record_event(EVENT_RECOVERY, "tcp teleop follower startup position captured")

    def validate_action_keys(self, action: Mapping[str, float]) -> None:
        """Ensure incoming action keys match the follower's known joints."""
        if not self.settings.require_action_keys_match or self.last_action is None:
            return
        expected = set(self.last_action)
        actual = set(action)
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        if missing or extra:
            raise ProtocolError(
                "ACTION keys do not match follower joints. "
                f"missing={missing} extra={extra}"
            )

    def validate_first_action_delta(self, action: Mapping[str, float]) -> None:
        """Block startup when leader/follower poses are too far apart."""
        if self.last_frame_id is not None or self.last_action is None:
            return
        max_key = ""
        max_delta = 0.0
        max_leader_value = 0.0
        max_follower_value = 0.0
        for key, value in action.items():
            if key not in self.last_action:
                continue
            leader_value = float(value)
            follower_value = self.last_action[key]
            delta = abs(leader_value - follower_value)
            if delta > max_delta:
                max_key = key
                max_delta = delta
                max_leader_value = leader_value
                max_follower_value = follower_value
        if max_delta > self.settings.max_first_action_delta:
            raise ProtocolError(
                "First ACTION is too far from follower startup position "
                f"({max_key}: leader={max_leader_value:.3f}, "
                f"follower={max_follower_value:.3f}, "
                f"delta={max_delta:.3f} > {self.settings.max_first_action_delta:.3f}). "
                "Move leader and follower to similar safe poses or fix calibration/mapping before teleoperation."
            )

    def limit_action_delta(self, target_action: Mapping[str, float]) -> dict[str, float]:
        """Clamp target action relative to the last sent follower action."""
        if self.last_action is None:
            return dict(target_action)

        limited: dict[str, float] = {}
        max_delta = self.settings.max_action_delta
        clamped = False
        for key, target_value in target_action.items():
            previous = self.last_action.get(key)
            if previous is None:
                limited[key] = float(target_value)
                continue
            delta = float(target_value) - previous
            if delta > max_delta:
                limited[key] = previous + max_delta
                clamped = True
            elif delta < -max_delta:
                limited[key] = previous - max_delta
                clamped = True
            else:
                limited[key] = float(target_value)
        if clamped:
            self._record_event(EVENT_EXCEPTION, "tcp teleop action delta limited")
        return limited

    def build_ack_message(self, action_message: Mapping[str, object]) -> dict[str, object]:
        """Build an ACK response for an ACTION message."""
        return {
            "type": MSG_ACK,
            "frame_id": action_message.get("frame_id"),
            "timestamp_ns": time.time_ns(),
            "follower_id": self.settings.follower_id,
        }

    def _handle_timeout(self) -> None:
        if not self.settings.hold_last_action_on_timeout or self.last_action is None:
            self._record_event(EVENT_EXCEPTION, "tcp teleop follower timeout without action")
            return
        self.follower_robot.send_action(self.last_action)
        self._record_event(EVENT_EXCEPTION, "tcp teleop follower timeout; holding last action")

    def _record_event(self, event_type: str, message: str) -> None:
        if self.recorder is not None:
            severity = "warning" if event_type == EVENT_EXCEPTION else "info"
            self.recorder.record_event(MetricEvent(event_type, message, severity=severity))

    def _record_sample(self, name: str, value: float, tags: Mapping[str, str]) -> None:
        if self.recorder is not None:
            self.recorder.record_sample(MetricSample(name, value, "ms", tags=dict(tags)))

    def _update_connection(self, status: str) -> None:
        if self.state is not None:
            self.state.update_connection(status)
