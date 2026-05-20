"""Dataset action sources for TCP replay."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

from ..config.schema import DatasetReplayConfig
from ..teleop.actions import normalize_teleop_action


class DatasetReplayError(RuntimeError):
    """Raised when dataset replay cannot safely produce action frames."""


@dataclass(frozen=True)
class ReplayFrame:
    """One action frame selected from a dataset episode."""

    frame_id: int
    dataset_index: int
    action: dict[str, float]
    timestamp_s: float | None = None


@dataclass(frozen=True)
class ReplaySourceInfo:
    """Metadata about the dataset selection being replayed."""

    dataset_path: str
    episode: int
    start_frame: int
    end_frame: int
    frame_count: int
    timing: str
    replay_frequency: float
    source_fps: float | None = None


def require_dataset_path(dataset: DatasetReplayConfig) -> Path:
    """Return an existing dataset path or fail before any network side effects."""
    if not dataset.path:
        raise DatasetReplayError("dataset.path is required for dataset replay.")
    path = Path(dataset.path).expanduser()
    if not path.exists():
        raise DatasetReplayError(
            f"dataset.path does not exist: {path}. "
            "Create or download the LeRobot dataset locally before running TCP replay."
        )
    if not path.is_dir():
        raise DatasetReplayError(f"dataset.path must be a directory: {path}.")
    return path


class InMemoryDatasetActionSource:
    """Small deterministic action source for tests and dry fake replay."""

    def __init__(
        self,
        actions: Sequence[Any],
        *,
        dataset_path: str = "memory://dataset",
        episode: int = 0,
        start_frame: int = 0,
        end_frame: int = -1,
        timing: str = "fixed_hz",
        replay_frequency: float = 30.0,
        timestamps_s: Sequence[float | None] | None = None,
    ) -> None:
        if timestamps_s is not None and len(timestamps_s) != len(actions):
            raise DatasetReplayError("timestamps_s length must match actions length.")
        selected_actions = _slice_actions(actions, start_frame=start_frame, end_frame=end_frame)
        if timestamps_s is None:
            selected_timestamps: Sequence[float | None] = [None] * len(selected_actions)
        else:
            selected_timestamps = _slice_actions(
                timestamps_s, start_frame=start_frame, end_frame=end_frame
            )
        if timing == "source_timestamps" and any(value is None for value in selected_timestamps):
            raise DatasetReplayError(
                "dataset.timing=source_timestamps requires timestamp metadata for every frame."
            )
        self._frames = [
            ReplayFrame(
                frame_id=index,
                dataset_index=start_frame + index,
                action=normalize_teleop_action(action),
                timestamp_s=None if timestamp is None else float(timestamp),
            )
            for index, (action, timestamp) in enumerate(zip(selected_actions, selected_timestamps))
        ]
        self.info = ReplaySourceInfo(
            dataset_path=dataset_path,
            episode=episode,
            start_frame=start_frame,
            end_frame=end_frame,
            frame_count=len(self._frames),
            timing=timing,
            replay_frequency=replay_frequency,
            source_fps=None,
        )

    def __iter__(self) -> Iterator[ReplayFrame]:
        return iter(self._frames)

    @property
    def frame_count(self) -> int:
        return len(self._frames)


class LeRobotDatasetActionSource:
    """Read one LeRobot dataset episode through a narrow adapter boundary."""

    def __init__(self, dataset_config: DatasetReplayConfig) -> None:
        dataset_path = require_dataset_path(dataset_config)
        LeRobotDataset = _load_lerobot_dataset_class()
        repo_id = _infer_repo_id(dataset_path)
        try:
            dataset = LeRobotDataset(
                repo_id,
                root=dataset_path,
                episodes=[dataset_config.episode],
                local_files_only=True,
            )
        except TypeError:
            try:
                dataset = LeRobotDataset(repo_id, root=dataset_path, episodes=[dataset_config.episode])
            except Exception as exc:
                raise _dataset_open_error(dataset_path, exc) from exc
        except Exception as exc:
            raise _dataset_open_error(dataset_path, exc) from exc

        self._dataset = dataset
        self._indices = _selected_dataset_indices(dataset, dataset_config)
        self._timing = dataset_config.timing
        self._frames = list(self._iter_loaded_frames(dataset_config, dataset_path))
        source_fps = _optional_float(getattr(dataset, "fps", None))
        if source_fps is None:
            source_fps = _optional_float(getattr(getattr(dataset, "meta", None), "fps", None))
        self.info = ReplaySourceInfo(
            dataset_path=str(dataset_path),
            episode=dataset_config.episode,
            start_frame=dataset_config.start_frame,
            end_frame=dataset_config.end_frame,
            frame_count=len(self._frames),
            timing=dataset_config.timing,
            replay_frequency=dataset_config.replay_frequency,
            source_fps=source_fps,
        )

    def __iter__(self) -> Iterator[ReplayFrame]:
        return iter(self._frames)

    @property
    def frame_count(self) -> int:
        return len(self._frames)

    def _iter_loaded_frames(
        self,
        dataset_config: DatasetReplayConfig,
        dataset_path: Path,
    ) -> Iterable[ReplayFrame]:
        previous_timestamp: float | None = None
        for frame_id, dataset_index in enumerate(self._indices):
            try:
                sample = self._dataset[dataset_index]
            except Exception as exc:
                raise DatasetReplayError(
                    f"Failed to read dataset frame {dataset_index} from {dataset_path}."
                ) from exc
            if not isinstance(sample, Mapping) or "action" not in sample:
                raise DatasetReplayError(
                    f"Dataset frame {dataset_index} does not contain an 'action' field."
                )
            action = normalize_teleop_action(sample["action"])
            timestamp_s = _sample_timestamp_s(sample)
            if dataset_config.timing == "source_timestamps":
                if timestamp_s is None:
                    raise DatasetReplayError(
                        "dataset.timing=source_timestamps requires timestamp metadata "
                        f"for frame {dataset_index}."
                    )
                if previous_timestamp is not None and timestamp_s < previous_timestamp:
                    raise DatasetReplayError("Dataset source timestamps must be non-decreasing.")
                previous_timestamp = timestamp_s
            yield ReplayFrame(
                frame_id=frame_id,
                dataset_index=dataset_index,
                action=action,
                timestamp_s=timestamp_s,
            )


def _slice_actions(
    values: Sequence[Any],
    *,
    start_frame: int,
    end_frame: int,
) -> Sequence[Any]:
    if start_frame < 0:
        raise DatasetReplayError("dataset.start_frame must be >= 0.")
    if end_frame != -1 and end_frame < start_frame:
        raise DatasetReplayError("dataset.end_frame must be -1 or >= dataset.start_frame.")
    stop = None if end_frame == -1 else end_frame + 1
    return values[start_frame:stop]


def _load_lerobot_dataset_class() -> Any:
    try:
        from lerobot.datasets import LeRobotDataset

        return LeRobotDataset
    except ImportError:
        try:
            from lerobot.datasets.lerobot_dataset import LeRobotDataset

            return LeRobotDataset
        except ImportError as exc:
            raise DatasetReplayError(
                "LeRobot is not installed or does not expose LeRobotDataset. "
                "Install LeRobot in this environment and run official replay preflight "
                "before TCP dataset replay."
            ) from exc


def _infer_repo_id(dataset_path: Path) -> str:
    parts = dataset_path.parts
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return dataset_path.name


def _dataset_open_error(dataset_path: Path, exc: Exception) -> DatasetReplayError:
    return DatasetReplayError(
        f"Failed to open LeRobot dataset at {dataset_path}: {exc}. "
        "Verify the local path with official LeRobot replay before TCP dataset replay."
    )


def _selected_dataset_indices(dataset: Any, dataset_config: DatasetReplayConfig) -> list[int]:
    episode_offset = dataset_config.start_frame
    episode_stop = None if dataset_config.end_frame == -1 else dataset_config.end_frame + 1
    meta = getattr(dataset, "meta", None)
    episodes = getattr(meta, "episodes", None)
    if isinstance(episodes, Mapping):
        from_indices = episodes.get("dataset_from_index")
        to_indices = episodes.get("dataset_to_index")
        try:
            from_index = int(_indexed_value(from_indices, dataset_config.episode))
            to_index = int(_indexed_value(to_indices, dataset_config.episode))
            relative = range(from_index, to_index)
            return list(relative)[episode_offset:episode_stop]
        except (TypeError, ValueError, KeyError, IndexError):
            pass

    num_frames = getattr(dataset, "num_frames", None)
    if num_frames is None:
        try:
            num_frames = len(dataset)
        except TypeError as exc:
            raise DatasetReplayError("Unable to determine LeRobot dataset frame count.") from exc
    return list(range(int(num_frames)))[episode_offset:episode_stop]


def _indexed_value(values: Any, index: int) -> Any:
    if hasattr(values, "iloc"):
        return values.iloc[index]
    return values[index]


def _sample_timestamp_s(sample: Mapping[str, Any]) -> float | None:
    for key in ("timestamp", "timestamp_s"):
        if key in sample:
            return _optional_float(sample[key])
    return None


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    if hasattr(value, "item"):
        value = value.item()
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
