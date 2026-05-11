"""TCP remote teleoperation runtime for SO-101 leader/follower pairs."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
import math
from pathlib import Path
import socket
import time
from typing import Any, Mapping

from legacy.protocol import ProtocolError as LegacyProtocolError
from legacy.protocol import DEFAULT_ACTION_KEYS, normalize_action

from .config_schema import ConfigError, PlatformConfig
from .metrics import EVENT_EXCEPTION, EVENT_RECOVERY, LATENCY_MS, MetricEvent, MetricSample
from .network.protocol import MSG_ACK, MSG_ACTION, ProtocolError, recv_message, send_message
from .recorder import JsonlMetricsRecorder
from .starai import (
    STARAI_FOLLOWER_TYPES,
    STARAI_LEADER_TYPES,
    build_starai_follower_robot,
    build_starai_leader_device,
    is_starai_follower_type,
    is_starai_leader_type,
)
from .webui import DashboardState

SUPPORTED_TELEOP_FOLLOWER_TYPES = {"so101_follower", *STARAI_FOLLOWER_TYPES}
SUPPORTED_TELEOP_LEADER_TYPES = {"so101_leader", *STARAI_LEADER_TYPES}

@dataclass(frozen=True)
class TcpTeleopSettings:
    """Resolved TCP teleoperation settings."""

    host: str
    port: int
    timeout_s: float
    max_packet_size: int
    send_hz: float
    control_hz: float
    leader_id: str
    follower_id: str
    hold_last_action_on_timeout: bool
    max_action_delta: float
    max_first_action_delta: float
    action_min: float
    action_max: float
    require_action_keys_match: bool
    print_leader_actions: bool
    print_action_interval: int


def tcp_teleop_settings(config: PlatformConfig) -> TcpTeleopSettings:
    """Build validated TCP teleoperation settings from platform config."""
    if config.mode != "remote_teleoperation":
        raise ConfigError("TCP teleoperation requires experiment.mode=remote_teleoperation.")
    if not config.teleop.enabled:
        raise ConfigError("TCP teleoperation requires teleop.enabled=true.")
    if config.teleop.type not in SUPPORTED_TELEOP_LEADER_TYPES:
        raise ConfigError(
            "TCP teleoperation currently supports teleop.type one of: "
            f"{', '.join(sorted(SUPPORTED_TELEOP_LEADER_TYPES))}."
        )
    if config.robot.type not in SUPPORTED_TELEOP_FOLLOWER_TYPES:
        raise ConfigError(
            "TCP teleoperation currently supports robot.type one of: "
            f"{', '.join(sorted(SUPPORTED_TELEOP_FOLLOWER_TYPES))}."
        )
    if not config.robot.port:
        raise ConfigError("TCP teleoperation server requires robot.port for the follower.")
    if not config.teleop.port:
        raise ConfigError("TCP teleoperation client requires teleop.port for the leader.")

    return TcpTeleopSettings(
        host=config.network.server_host,
        port=config.network.server_port,
        timeout_s=config.network.timeout_ms / 1000.0,
        max_packet_size=config.network.max_packet_size_mb * 1024 * 1024,
        send_hz=config.runtime.action_send_frequency,
        control_hz=config.runtime.control_frequency,
        leader_id=config.teleop.id,
        follower_id=config.robot.id,
        hold_last_action_on_timeout=config.runtime.hold_last_action_on_timeout,
        max_action_delta=config.safety.max_action_delta,
        max_first_action_delta=config.safety.max_first_action_delta,
        action_min=config.safety.action_min,
        action_max=config.safety.action_max,
        require_action_keys_match=config.safety.require_action_keys_match,
        print_leader_actions=config.logging.print_leader_actions,
        print_action_interval=config.logging.print_action_interval,
    )


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


def build_so101_leader_device(config: PlatformConfig) -> Any:
    """Build and connect a LeRobot SO-101 leader teleop device."""
    SO101Leader, SO101LeaderConfig = _load_so101_leader_api()
    leader_config = _build_lerobot_device_config(
        SO101LeaderConfig,
        port=config.teleop.port,
        device_id=config.teleop.id,
        calibration_dir=config.teleop.calibration_dir,
    )
    leader = SO101Leader(leader_config)
    leader.connect()
    return leader


def build_so101_follower_robot(config: PlatformConfig) -> Any:
    """Build and connect a LeRobot SO-101 follower robot."""
    SO101Follower, SO101FollowerConfig = _load_so101_follower_api()
    follower_config = _build_lerobot_device_config(
        SO101FollowerConfig,
        port=config.robot.port,
        device_id=config.robot.id,
        calibration_dir=config.robot.calibration_dir,
    )
    follower = SO101Follower(follower_config)
    follower.connect()
    return follower


def _build_lerobot_device_config(
    ConfigClass: type,
    *,
    port: str | None,
    device_id: str,
    calibration_dir: str | None,
) -> object:
    kwargs: dict[str, object] = {"port": port, "id": device_id}
    if calibration_dir is not None:
        kwargs["calibration_dir"] = Path(calibration_dir)
    try:
        return ConfigClass(**kwargs)
    except TypeError:
        kwargs.pop("calibration_dir", None)
        return ConfigClass(**kwargs)


def build_teleop_leader_device(config: PlatformConfig) -> Any:
    """Build and connect the configured leader teleoperator."""
    if is_starai_leader_type(config.teleop.type):
        return build_starai_leader_device(config)
    return build_so101_leader_device(config)


def build_teleop_follower_robot(config: PlatformConfig) -> Any:
    """Build and connect the configured follower robot."""
    if is_starai_follower_type(config.robot.type):
        return build_starai_follower_robot(config)
    return build_so101_follower_robot(config)


def normalize_teleop_action(action: Any) -> dict[str, float]:
    """Normalize teleoperation actions while allowing non-SO-101 dict keys."""
    if isinstance(action, Mapping):
        if all(key in action for key in DEFAULT_ACTION_KEYS):
            return normalize_action(action)
        try:
            return {str(key): float(value) for key, value in action.items()}
        except (TypeError, ValueError) as exc:
            raise ProtocolError("Action dict values must be numeric.") from exc
    try:
        return normalize_action(action)
    except LegacyProtocolError as exc:
        raise ProtocolError(str(exc)) from exc


def validate_action_values(
    action: Mapping[str, float],
    *,
    action_min: float,
    action_max: float,
) -> None:
    """Reject non-finite or out-of-range action values."""
    for key, value in action.items():
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ProtocolError(f"ACTION value for {key} is not finite: {value!r}.")
        if numeric < action_min or numeric > action_max:
            raise ProtocolError(
                f"ACTION value for {key}={numeric:.3f} is outside "
                f"[{action_min:.3f}, {action_max:.3f}]."
            )


def _load_so101_leader_api() -> tuple[type, type]:
    module_names = (
        "lerobot.teleoperators.so_leader",
        "lerobot.teleoperators.so101_leader",
        "lerobot.teleoperators.so101_leader.configuration_so101_leader",
    )
    for module_name in module_names:
        try:
            module = import_module(module_name)
            return module.SO101Leader, module.SO101LeaderConfig
        except ImportError:
            continue
    raise RuntimeError("Failed to import LeRobot SO101Leader. Install lerobot on the leader machine.")


def _load_so101_follower_api() -> tuple[type, type]:
    module_names = (
        "lerobot.robots.so_follower",
        "lerobot.robots.so101_follower",
        "lerobot.robots.so101_follower.configuration_so101_follower",
    )
    for module_name in module_names:
        try:
            module = import_module(module_name)
            return module.SO101Follower, module.SO101FollowerConfig
        except ImportError:
            continue
    raise RuntimeError("Failed to import LeRobot SO101Follower. Install lerobot on the follower machine.")
