"""Runtime orchestration for TCP dataset replay."""

from __future__ import annotations

from dataclasses import asdict
from typing import Callable

from ..config.schema import PlatformConfig
from ..recording.recorder import JsonlMetricsRecorder
from ..reliability import STAGE_NETWORK, record_exception_event
from ..replay import DatasetReplayTcpClient, LeRobotDatasetActionSource, ReplaySourceInfo
from ..teleop import tcp_teleop_settings
from ..webui import DashboardState
from .common import build_configured_metadata, copy_source_config, create_configured_run_dir

SourceFactory = Callable[[PlatformConfig], object]


def run_dataset_replay_client(
    config: PlatformConfig,
    source_factory: SourceFactory | None = None,
) -> int:
    """Replay one configured dataset episode through the TCP follower path."""
    recorder: JsonlMetricsRecorder | None = None
    try:
        settings = tcp_teleop_settings(config)
        run_dir = create_configured_run_dir(config, "dataset-replay-client")
        metadata = build_configured_metadata("dataset-replay-client", config, run_dir)
        metadata["extra"] = {
            **dict(metadata.get("extra", {})),
            "dataset_replay": _requested_dataset_metadata(config),
            "tcp_endpoint": config.network.endpoint,
            "safety": _safety_metadata(config),
        }
        recorder = JsonlMetricsRecorder(run_dir, metadata=metadata)
        copy_source_config(config, run_dir)

        source = (source_factory or _default_source_factory)(config)
        source_info = getattr(source, "info", None)
        if not isinstance(source_info, ReplaySourceInfo):
            raise TypeError("Dataset replay source must expose ReplaySourceInfo as .info.")
        recorder.update_metadata(
            {
                "extra": {
                    **dict(recorder.metadata.get("extra", {})),
                    "dataset_replay": asdict(source_info),
                    "tcp_endpoint": config.network.endpoint,
                    "safety": _safety_metadata(config),
                }
            }
        )

        state = DashboardState.from_config(config, "dataset-replay-client")
        print(f"Run directory: {run_dir}")
        print(f"Dataset replay client connecting to {settings.host}:{settings.port}")
        print(
            "Dataset replay: "
            f"path={source_info.dataset_path} episode={source_info.episode} "
            f"frames={source_info.frame_count} timing={source_info.timing}"
        )
        client = DatasetReplayTcpClient(
            frames=source,
            source_info=source_info,
            settings=settings,
            recorder=recorder,
            state=state,
        )
        result = client.run()
        recorder.write_summary()
        return result
    except KeyboardInterrupt:
        if recorder is not None:
            recorder.write_summary()
        return 0
    except Exception as exc:
        if recorder is not None:
            record_exception_event(
                recorder,
                stage=STAGE_NETWORK,
                component="dataset_replay_client",
                exc=exc,
            )
            recorder.write_summary()
        raise
    finally:
        if recorder is not None:
            recorder.close()


def _default_source_factory(config: PlatformConfig) -> LeRobotDatasetActionSource:
    return LeRobotDatasetActionSource(config.dataset)


def _requested_dataset_metadata(config: PlatformConfig) -> dict[str, object]:
    return {
        "dataset_path": config.dataset.path,
        "episode": config.dataset.episode,
        "start_frame": config.dataset.start_frame,
        "end_frame": config.dataset.end_frame,
        "frame_count": None,
        "timing": config.dataset.timing,
        "replay_frequency": config.dataset.replay_frequency,
        "source_fps": None,
    }


def _safety_metadata(config: PlatformConfig) -> dict[str, object]:
    return {
        "max_action_delta": config.safety.max_action_delta,
        "max_first_action_delta": config.safety.max_first_action_delta,
        "action_min": config.safety.action_min,
        "action_max": config.safety.action_max,
        "require_action_keys_match": config.safety.require_action_keys_match,
    }
