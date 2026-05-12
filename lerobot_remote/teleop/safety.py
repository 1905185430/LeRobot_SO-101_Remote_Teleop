"""Safety validation helpers for TCP teleoperation."""

from __future__ import annotations

import math
from typing import Mapping

from ..network.protocol import ProtocolError


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
