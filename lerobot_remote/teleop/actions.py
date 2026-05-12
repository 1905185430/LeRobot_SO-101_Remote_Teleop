"""Teleoperation action normalization."""

from __future__ import annotations

from typing import Any, Mapping

from legacy.protocol import ProtocolError as LegacyProtocolError
from legacy.protocol import DEFAULT_ACTION_KEYS, normalize_action

from ..network.protocol import ProtocolError


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
