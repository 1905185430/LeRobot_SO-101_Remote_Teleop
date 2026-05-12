"""TCP teleoperation leader client."""

from __future__ import annotations

import socket
import time
from typing import Any, Mapping

from ..network.protocol import MSG_ACK, MSG_ACTION, ProtocolError, recv_message, send_message
from ..recording.metrics import LATENCY_MS, MetricEvent, MetricSample, EVENT_RECOVERY
from ..recording.recorder import JsonlMetricsRecorder
from ..webui.state import DashboardState
from .actions import normalize_teleop_action
from .safety import validate_action_values
from .settings import TcpTeleopSettings


class TcpTeleopLeaderClient:
    """Read leader actions and stream them to a TCP follower server."""

    def __init__(
        self,
        leader_device: Any,
        settings: TcpTeleopSettings,
        recorder: JsonlMetricsRecorder | None = None,
        state: DashboardState | None = None,
    ) -> None:
        self.leader_device = leader_device
        self.settings = settings
        self.recorder = recorder
        self.state = state
        self.seq = 0

    def run(self, max_messages: int | None = None) -> int:
        """Run the leader send loop until interrupted or max_messages is reached."""
        period_s = 1.0 / self.settings.send_hz
        sent = 0
        with socket.create_connection(
            (self.settings.host, self.settings.port),
            timeout=self.settings.timeout_s,
        ) as sock:
            sock.settimeout(self.settings.timeout_s)
            self._record_event(EVENT_RECOVERY, "tcp teleop leader connected")
            self._update_connection("connected")
            next_tick = time.perf_counter()
            while max_messages is None or sent < max_messages:
                started = time.perf_counter()
                message = self.build_action_message()
                self.maybe_print_leader_action(message)
                send_message(sock, message, max_size=self.settings.max_packet_size)
                ack = recv_message(sock, max_size=self.settings.max_packet_size)
                self._validate_ack(ack, message["frame_id"])
                rtt_ms = (time.perf_counter() - started) * 1000.0
                self._record_sample(LATENCY_MS, rtt_ms, {"component": "tcp_teleop_leader"})
                if self.state is not None:
                    self.state.update_action(message)
                    self.state.update_latency(rtt_ms)
                sent += 1

                next_tick += period_s
                sleep_s = next_tick - time.perf_counter()
                if sleep_s > 0:
                    time.sleep(sleep_s)
                else:
                    next_tick = time.perf_counter()
        self._update_connection("closed")
        return 0

    def build_action_message(self) -> dict[str, object]:
        """Read one leader action and convert it to protocol message."""
        action = self.read_safe_leader_action()
        frame_id = self.seq
        self.seq += 1
        return {
            "type": MSG_ACTION,
            "frame_id": frame_id,
            "timestamp_ns": time.time_ns(),
            "leader_id": self.settings.leader_id,
            "action": action,
        }

    def read_safe_leader_action(self) -> dict[str, float]:
        """Read and validate one leader action before network send."""
        try:
            raw_action = self.leader_device.get_action()
            action = normalize_teleop_action(raw_action)
            validate_action_values(
                action,
                action_min=self.settings.action_min,
                action_max=self.settings.action_max,
            )
        except Exception as exc:
            raise RuntimeError(
                "Failed to read a safe leader action. No command was sent to the follower. "
                "For StarAI this usually means one or more leader motors returned no position. "
                "Check the leader serial port, power, motor IDs, calibration, and StarAI/FashionStar "
                "SDK hotfixes before retrying."
            ) from exc
        return action

    def maybe_print_leader_action(self, message: Mapping[str, object]) -> None:
        """Print outgoing leader action at a configured interval."""
        if not self.settings.print_leader_actions:
            return
        frame_id = message.get("frame_id")
        if not isinstance(frame_id, int):
            return
        if frame_id % self.settings.print_action_interval != 0:
            return
        action = message.get("action", {})
        if not isinstance(action, Mapping):
            return
        formatted = ", ".join(f"{key}={float(value):.3f}" for key, value in sorted(action.items()))
        print(f"Leader action frame={frame_id}: {formatted}", flush=True)

    def _validate_ack(self, ack: Mapping[str, object], frame_id: object) -> None:
        if ack.get("type") != MSG_ACK:
            raise ProtocolError(f"Expected ACK response, got {ack.get('type')!r}.")
        if ack.get("frame_id") != frame_id:
            raise ProtocolError(f"ACK frame_id mismatch: {ack.get('frame_id')!r} != {frame_id!r}.")

    def _record_event(self, event_type: str, message: str) -> None:
        if self.recorder is not None:
            self.recorder.record_event(MetricEvent(event_type, message))

    def _record_sample(self, name: str, value: float, tags: Mapping[str, str]) -> None:
        if self.recorder is not None:
            self.recorder.record_sample(MetricSample(name, value, "ms", tags=dict(tags)))

    def _update_connection(self, status: str) -> None:
        if self.state is not None:
            self.state.update_connection(status)
