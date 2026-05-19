"""Teleoperation action normalization."""

from __future__ import annotations

from typing import Any, Mapping

from ..network.protocol import ProtocolError

EXPECTED_SO101_ACTION_LENGTH = 6
SO101_ACTION_KEYS = (
    "shoulder_pan.pos",
    "shoulder_lift.pos",
    "elbow_flex.pos",
    "wrist_flex.pos",
    "wrist_roll.pos",
    "gripper.pos",
)


def normalize_teleop_action(action: Any) -> dict[str, float]:
    """Normalize teleoperation actions while allowing non-SO-101 dict keys."""
    if isinstance(action, Mapping):
        if all(key in action for key in SO101_ACTION_KEYS):
            return _normalize_so101_action(action)
        try:
            return {str(key): float(value) for key, value in action.items()}
        except (TypeError, ValueError) as exc:
            raise ProtocolError("Action dict values must be numeric.") from exc
    return _normalize_so101_action(action)


def _normalize_so101_action(action: Any) -> dict[str, float]:
    if isinstance(action, Mapping):
        missing_keys = [key for key in SO101_ACTION_KEYS if key not in action]
        if missing_keys:
            raise ProtocolError(f"Action dict missing expected keys: {', '.join(missing_keys)}.")
        values = [action[key] for key in SO101_ACTION_KEYS]
    else:
        values = action.tolist() if hasattr(action, "tolist") else action

    try:
        normalized_values = [float(value) for value in values]
    except TypeError as exc:
        raise ProtocolError("Action must be an iterable of numeric values.") from exc
    except ValueError as exc:
        raise ProtocolError("Action values must be numeric.") from exc

    if len(normalized_values) != EXPECTED_SO101_ACTION_LENGTH:
        raise ProtocolError(
            f"Expected action length {EXPECTED_SO101_ACTION_LENGTH}, got {len(normalized_values)}."
        )

    return dict(zip(SO101_ACTION_KEYS, normalized_values))
