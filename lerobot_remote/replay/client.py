"""TCP client for replaying dataset action frames."""

from __future__ import annotations

import socket
import time
from typing import Iterable, Mapping

from ..network.protocol import MSG_ACK, MSG_ACTION, ProtocolError, recv_message, send_message
from ..recording.metrics import EVENT_RECOVERY, LATENCY_MS, MetricEvent, MetricSample
from ..recording.recorder import JsonlMetricsRecorder
from ..teleop.safety import validate_action_values
from ..teleop.settings import TcpTeleopSettings
from ..webui.state import DashboardState
from .dataset import ReplayFrame, ReplaySourceInfo

EVENT_DATASET_REPLAY_START = "dataset_replay_start"
EVENT_DATASET_REPLAY_COMPLETE = "dataset_replay_complete"


class DatasetReplayTcpClient:
    """Stream selected dataset action frames to a TCP teleop follower."""

    def __init__(
        self,
        frames: Iterable[ReplayFrame],
        source_info: ReplaySourceInfo,
        settings: TcpTeleopSettings,
        recorder: JsonlMetricsRecorder | None = None,
        state: DashboardState | None = None,
    ) -> None:
        self.frames = frames
        self.source_info = source_info
        self.settings = settings
        self.recorder = recorder
        self.state = state

    def run(self) -> int:
        """Send all selected dataset frames and stop after the episode is exhausted."""
        frame_count = 0
        with socket.create_connection(
            (self.settings.host, self.settings.port),
            timeout=self.settings.timeout_s,
        ) as sock:
            sock.settimeout(self.settings.timeout_s)
            self._record_event(EVENT_RECOVERY, "dataset replay TCP client connected")
            self._record_event(
                EVENT_DATASET_REPLAY_START,
                "dataset replay started",
                {
                    "dataset_path": self.source_info.dataset_path,
                    "episode": str(self.source_info.episode),
                    "timing": self.source_info.timing,
                },
            )
            self._update_connection("connected")
            next_tick = time.perf_counter()
            previous_timestamp_s: float | None = None
            for frame in self.frames:
                started = time.perf_counter()
                message = self.build_action_message(frame)
                send_message(sock, message, max_size=self.settings.max_packet_size)
                ack = recv_message(sock, max_size=self.settings.max_packet_size)
                self._validate_ack(ack, message["frame_id"])
                rtt_ms = (time.perf_counter() - started) * 1000.0
                self._record_sample(
                    LATENCY_MS,
                    rtt_ms,
                    {
                        "component": "dataset_replay_client",
                        "dataset_frame": str(frame.dataset_index),
                    },
                )
                if self.state is not None:
                    self.state.update_action(message)
                    self.state.update_latency(rtt_ms)
                frame_count += 1
                next_tick, previous_timestamp_s = self._sleep_until_next_frame(
                    frame,
                    next_tick,
                    previous_timestamp_s,
                )
        self._record_event(
            EVENT_DATASET_REPLAY_COMPLETE,
            "dataset replay completed",
            {"frames_sent": str(frame_count)},
        )
        self._update_connection("closed")
        return 0

    def build_action_message(self, frame: ReplayFrame) -> dict[str, object]:
        """Validate and convert one dataset frame to a TCP ACTION message."""
        validate_action_values(
            frame.action,
            action_min=self.settings.action_min,
            action_max=self.settings.action_max,
        )
        return {
            "type": MSG_ACTION,
            "frame_id": frame.frame_id,
            "timestamp_ns": time.time_ns(),
            "leader_id": self.settings.leader_id,
            "dataset_frame": frame.dataset_index,
            "action": dict(frame.action),
        }

    def _sleep_until_next_frame(
        self,
        frame: ReplayFrame,
        next_tick: float,
        previous_timestamp_s: float | None,
    ) -> tuple[float, float | None]:
        if self.source_info.timing == "source_timestamps":
            if frame.timestamp_s is None:
                raise ProtocolError("source_timestamps replay requires frame timestamps.")
            if previous_timestamp_s is not None:
                sleep_s = max(0.0, frame.timestamp_s - previous_timestamp_s)
                if sleep_s > 0:
                    time.sleep(sleep_s)
            return time.perf_counter(), frame.timestamp_s

        period_s = 1.0 / self.source_info.replay_frequency
        next_tick += period_s
        sleep_s = next_tick - time.perf_counter()
        if sleep_s > 0:
            time.sleep(sleep_s)
        else:
            next_tick = time.perf_counter()
        return next_tick, previous_timestamp_s

    def _validate_ack(self, ack: Mapping[str, object], frame_id: object) -> None:
        if ack.get("type") != MSG_ACK:
            raise ProtocolError(f"Expected ACK response, got {ack.get('type')!r}.")
        if ack.get("frame_id") != frame_id:
            raise ProtocolError(f"ACK frame_id mismatch: {ack.get('frame_id')!r} != {frame_id!r}.")

    def _record_event(
        self,
        event_type: str,
        message: str,
        details: Mapping[str, str] | None = None,
    ) -> None:
        if self.recorder is not None:
            self.recorder.record_event(
                MetricEvent(event_type, message, details=dict(details or {}))
            )

    def _record_sample(self, name: str, value: float, tags: Mapping[str, str]) -> None:
        if self.recorder is not None:
            self.recorder.record_sample(MetricSample(name, value, "ms", tags=dict(tags)))

    def _update_connection(self, status: str) -> None:
        if self.state is not None:
            self.state.update_connection(status)
