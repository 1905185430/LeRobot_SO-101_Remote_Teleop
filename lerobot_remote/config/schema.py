"""Schema objects for config-driven platform modes."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


VALID_MODES = {
    "local_inference",
    "remote_inference",
    "remote_teleoperation",
    "data_recording",
    "debug_mock",
}
VALID_NETWORK_PROTOCOLS = {"tcp"}
VALID_DATASET_TIMING_MODES = {"fixed_hz", "source_timestamps"}


class ConfigError(ValueError):
    """Raised when a platform config is missing required fields or invalid."""


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    mode: str
    task_name: str = ""
    save_dir: str = "logs/experiments"


@dataclass(frozen=True)
class RobotConfig:
    type: str
    port: str | None = None
    id: str = ""
    calibration_dir: str | None = None
    skip_initial_position: bool = False


@dataclass(frozen=True)
class TeleopConfig:
    enabled: bool = False
    type: str | None = None
    port: str | None = None
    id: str = ""
    calibration_dir: str | None = None


@dataclass(frozen=True)
class ModelConfig:
    type: str
    model_path: str = ""
    device: str = "cuda"
    dtype: str = "float32"
    action_horizon: int = 30
    inference_frequency: float = 10.0


@dataclass(frozen=True)
class CameraDeviceConfig:
    type: str = "opencv"
    index: int | str = 0
    width: int = 640
    height: int = 480
    fps: int = 30


@dataclass(frozen=True)
class CameraConfig:
    enabled: bool = True
    fps: int = 30
    cameras: dict[str, CameraDeviceConfig] = field(default_factory=dict)


@dataclass(frozen=True)
class NetworkConfig:
    protocol: str = "tcp"
    server_host: str = "127.0.0.1"
    server_port: int = 9000
    timeout_ms: int = 200
    reconnect: bool = True
    max_packet_size_mb: int = 16

    @property
    def endpoint(self) -> str:
        return f"{self.server_host}:{self.server_port}"


@dataclass(frozen=True)
class RuntimeConfig:
    control_frequency: float = 30.0
    observation_frequency: float = 30.0
    action_send_frequency: float = 30.0
    safety_stop_on_timeout: bool = True
    hold_last_action_on_timeout: bool = True


@dataclass(frozen=True)
class SafetyConfig:
    max_action_delta: float = 2.0
    max_first_action_delta: float = 25.0
    action_min: float = -100.0
    action_max: float = 100.0
    require_action_keys_match: bool = True


@dataclass(frozen=True)
class WebUIConfig:
    enabled: bool = False
    host: str = "0.0.0.0"
    port: int = 7860
    show_images: bool = True
    show_joint_states: bool = True
    show_latency: bool = True
    show_actions: bool = True


@dataclass(frozen=True)
class LoggingConfig:
    save_video: bool = False
    save_metrics: bool = True
    save_observations: bool = False
    save_actions: bool = True
    log_level: str = "info"
    print_leader_actions: bool = False
    print_action_interval: int = 10


@dataclass(frozen=True)
class DatasetReplayConfig:
    path: str | None = None
    episode: int = 0
    start_frame: int = 0
    end_frame: int = -1
    timing: str = "fixed_hz"
    replay_frequency: float = 30.0


@dataclass(frozen=True)
class PlatformConfig:
    experiment: ExperimentConfig
    robot: RobotConfig
    teleop: TeleopConfig
    model: ModelConfig
    camera: CameraConfig
    network: NetworkConfig
    runtime: RuntimeConfig
    safety: SafetyConfig
    webui: WebUIConfig
    logging: LoggingConfig
    dataset: DatasetReplayConfig
    source_path: Path | None = None

    @property
    def mode(self) -> str:
        return self.experiment.mode

    def summary(self) -> dict[str, object]:
        """Return a compact operator-facing config summary."""
        return {
            "name": self.experiment.name,
            "mode": self.experiment.mode,
            "task_name": self.experiment.task_name,
            "robot": self.robot.type,
            "model": self.model.type,
            "network": {
                "protocol": self.network.protocol,
                "endpoint": self.network.endpoint,
            },
            "camera_names": sorted(self.camera.cameras),
            "webui_enabled": self.webui.enabled,
            "dataset": {
                "path": self.dataset.path,
                "episode": self.dataset.episode,
                "start_frame": self.dataset.start_frame,
                "end_frame": self.dataset.end_frame,
                "timing": self.dataset.timing,
                "replay_frequency": self.dataset.replay_frequency,
            },
            "source_path": None if self.source_path is None else str(self.source_path),
        }


def platform_config_from_mapping(
    data: Mapping[str, Any], source_path: str | Path | None = None
) -> PlatformConfig:
    """Build and validate a platform config from nested mapping data."""
    experiment = _experiment(_section(data, "experiment", required=True))
    robot = _robot(_section(data, "robot", required=True))
    teleop = _teleop(_section(data, "teleop"))
    model = _model(_section(data, "model", required=True))
    camera = _camera(_section(data, "camera"))
    network = _network(_section(data, "network"))
    runtime = _runtime(_section(data, "runtime"))
    safety = _safety(_section(data, "safety"))
    webui = _webui(_section(data, "webui"))
    logging = _logging(_section(data, "logging"))
    dataset = _dataset(_section(data, "dataset"), has_section="dataset" in data)

    _validate_mode(experiment, teleop)
    return PlatformConfig(
        experiment=experiment,
        robot=robot,
        teleop=teleop,
        model=model,
        camera=camera,
        network=network,
        runtime=runtime,
        safety=safety,
        webui=webui,
        logging=logging,
        dataset=dataset,
        source_path=None if source_path is None else Path(source_path),
    )


def _section(data: Mapping[str, Any], name: str, required: bool = False) -> Mapping[str, Any]:
    value = data.get(name, {})
    if value in (None, ""):
        value = {}
    if not isinstance(value, Mapping):
        raise ConfigError(f"Section '{name}' must be a mapping.")
    if required and not value:
        raise ConfigError(f"Missing required section '{name}'.")
    return value


def _experiment(data: Mapping[str, Any]) -> ExperimentConfig:
    return ExperimentConfig(
        name=_str(data, "name", required=True),
        mode=_str(data, "mode", required=True),
        task_name=_str(data, "task_name", default=""),
        save_dir=_str(data, "save_dir", default="logs/experiments"),
    )


def _robot(data: Mapping[str, Any]) -> RobotConfig:
    return RobotConfig(
        type=_str(data, "type", required=True),
        port=_optional_str(data, "port"),
        id=_str(data, "id", default=""),
        calibration_dir=_optional_str(data, "calibration_dir"),
        skip_initial_position=_bool(data, "skip_initial_position", default=False),
    )


def _teleop(data: Mapping[str, Any]) -> TeleopConfig:
    return TeleopConfig(
        enabled=_bool(data, "enabled", default=False),
        type=_optional_str(data, "type"),
        port=_optional_str(data, "port"),
        id=_str(data, "id", default=""),
        calibration_dir=_optional_str(data, "calibration_dir"),
    )


def _model(data: Mapping[str, Any]) -> ModelConfig:
    return ModelConfig(
        type=_str(data, "type", required=True),
        model_path=_str(data, "model_path", default=""),
        device=_str(data, "device", default="cuda"),
        dtype=_str(data, "dtype", default="float32"),
        action_horizon=_int(data, "action_horizon", default=30),
        inference_frequency=_float(data, "inference_frequency", default=10.0),
    )


def _camera(data: Mapping[str, Any]) -> CameraConfig:
    cameras_raw = data.get("cameras", {})
    if cameras_raw in (None, ""):
        cameras_raw = {}
    if not isinstance(cameras_raw, Mapping):
        raise ConfigError("Section 'camera.cameras' must be a mapping.")

    cameras = {
        str(name): CameraDeviceConfig(
            type=_str(camera_data, "type", default="opencv"),
            index=_index(camera_data, "index", default=0),
            width=_int(camera_data, "width", default=640),
            height=_int(camera_data, "height", default=480),
            fps=_int(camera_data, "fps", default=_int(data, "fps", default=30)),
        )
        for name, camera_data in cameras_raw.items()
        if isinstance(camera_data, Mapping)
    }
    if len(cameras) != len(cameras_raw):
        raise ConfigError("Every camera entry must be a mapping.")

    return CameraConfig(
        enabled=_bool(data, "enabled", default=True),
        fps=_int(data, "fps", default=30),
        cameras=cameras,
    )


def _network(data: Mapping[str, Any]) -> NetworkConfig:
    network = NetworkConfig(
        protocol=_str(data, "protocol", default="tcp"),
        server_host=_str(data, "server_host", default="127.0.0.1"),
        server_port=_int(data, "server_port", default=9000),
        timeout_ms=_int(data, "timeout_ms", default=200),
        reconnect=_bool(data, "reconnect", default=True),
        max_packet_size_mb=_int(data, "max_packet_size_mb", default=16),
    )
    if network.protocol not in VALID_NETWORK_PROTOCOLS:
        raise ConfigError(
            f"Unsupported network.protocol '{network.protocol}'. "
            f"Expected one of: {', '.join(sorted(VALID_NETWORK_PROTOCOLS))}."
        )
    if not 1 <= network.server_port <= 65535:
        raise ConfigError("network.server_port must be in [1, 65535].")
    return network


def _runtime(data: Mapping[str, Any]) -> RuntimeConfig:
    return RuntimeConfig(
        control_frequency=_float(data, "control_frequency", default=30.0),
        observation_frequency=_float(data, "observation_frequency", default=30.0),
        action_send_frequency=_float(data, "action_send_frequency", default=30.0),
        safety_stop_on_timeout=_bool(data, "safety_stop_on_timeout", default=True),
        hold_last_action_on_timeout=_bool(data, "hold_last_action_on_timeout", default=True),
    )


def _safety(data: Mapping[str, Any]) -> SafetyConfig:
    safety = SafetyConfig(
        max_action_delta=_float(data, "max_action_delta", default=2.0),
        max_first_action_delta=_float(data, "max_first_action_delta", default=25.0),
        action_min=_float(data, "action_min", default=-100.0),
        action_max=_float(data, "action_max", default=100.0),
        require_action_keys_match=_bool(data, "require_action_keys_match", default=True),
    )
    if safety.max_action_delta <= 0:
        raise ConfigError("safety.max_action_delta must be > 0.")
    if safety.max_first_action_delta <= 0:
        raise ConfigError("safety.max_first_action_delta must be > 0.")
    if safety.action_min >= safety.action_max:
        raise ConfigError("safety.action_min must be less than safety.action_max.")
    return safety


def _webui(data: Mapping[str, Any]) -> WebUIConfig:
    return WebUIConfig(
        enabled=_bool(data, "enabled", default=False),
        host=_str(data, "host", default="0.0.0.0"),
        port=_int(data, "port", default=7860),
        show_images=_bool(data, "show_images", default=True),
        show_joint_states=_bool(data, "show_joint_states", default=True),
        show_latency=_bool(data, "show_latency", default=True),
        show_actions=_bool(data, "show_actions", default=True),
    )


def _logging(data: Mapping[str, Any]) -> LoggingConfig:
    logging = LoggingConfig(
        save_video=_bool(data, "save_video", default=False),
        save_metrics=_bool(data, "save_metrics", default=True),
        save_observations=_bool(data, "save_observations", default=False),
        save_actions=_bool(data, "save_actions", default=True),
        log_level=_str(data, "log_level", default="info"),
        print_leader_actions=_bool(data, "print_leader_actions", default=False),
        print_action_interval=_int(data, "print_action_interval", default=10),
    )
    if logging.print_action_interval <= 0:
        raise ConfigError("logging.print_action_interval must be > 0.")
    return logging


def _dataset(data: Mapping[str, Any], *, has_section: bool) -> DatasetReplayConfig:
    path = _optional_str(data, "path")
    if has_section and path is None:
        raise ConfigError("dataset.path is required when dataset section is provided.")

    dataset = DatasetReplayConfig(
        path=path,
        episode=_int(data, "episode", default=0),
        start_frame=_int(data, "start_frame", default=0),
        end_frame=_int(data, "end_frame", default=-1),
        timing=_str(data, "timing", default="fixed_hz"),
        replay_frequency=_float(data, "replay_frequency", default=30.0),
    )
    if dataset.episode < 0:
        raise ConfigError("dataset.episode must be >= 0.")
    if dataset.start_frame < 0:
        raise ConfigError("dataset.start_frame must be >= 0.")
    if dataset.end_frame < -1:
        raise ConfigError("dataset.end_frame must be -1 or >= dataset.start_frame.")
    if dataset.end_frame != -1 and dataset.end_frame < dataset.start_frame:
        raise ConfigError("dataset.end_frame must be -1 or >= dataset.start_frame.")
    if dataset.timing not in VALID_DATASET_TIMING_MODES:
        raise ConfigError(
            f"Unsupported dataset.timing '{dataset.timing}'. "
            f"Expected one of: {', '.join(sorted(VALID_DATASET_TIMING_MODES))}."
        )
    if dataset.replay_frequency <= 0:
        raise ConfigError("dataset.replay_frequency must be > 0.")
    return dataset


def _validate_mode(experiment: ExperimentConfig, teleop: TeleopConfig) -> None:
    if experiment.mode not in VALID_MODES:
        raise ConfigError(
            f"Unsupported experiment.mode '{experiment.mode}'. "
            f"Expected one of: {', '.join(sorted(VALID_MODES))}."
        )
    if experiment.mode == "remote_teleoperation" and not teleop.enabled:
        raise ConfigError("remote_teleoperation mode requires teleop.enabled=true.")


def _str(data: Mapping[str, Any], key: str, default: str = "", required: bool = False) -> str:
    value = data.get(key, None)
    if value is None:
        if required:
            raise ConfigError(f"Missing required key '{key}'.")
        return default
    return str(value)


def _optional_str(data: Mapping[str, Any], key: str) -> str | None:
    value = data.get(key, None)
    if value in (None, ""):
        return None
    return str(value)


def _bool(data: Mapping[str, Any], key: str, default: bool = False) -> bool:
    value = data.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in {"true", "yes", "on", "1"}:
            return True
        if value.lower() in {"false", "no", "off", "0"}:
            return False
    raise ConfigError(f"Key '{key}' must be boolean.")


def _int(data: Mapping[str, Any], key: str, default: int) -> int:
    value = data.get(key, default)
    if isinstance(value, bool):
        raise ConfigError(f"Key '{key}' must be an integer.")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"Key '{key}' must be an integer.") from exc


def _float(data: Mapping[str, Any], key: str, default: float) -> float:
    value = data.get(key, default)
    if isinstance(value, bool):
        raise ConfigError(f"Key '{key}' must be numeric.")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"Key '{key}' must be numeric.") from exc


def _index(data: Mapping[str, Any], key: str, default: int | str) -> int | str:
    value = data.get(key, default)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return str(value)
