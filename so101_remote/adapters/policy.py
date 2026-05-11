"""Policy adapter boundary for future model integrations."""

from __future__ import annotations

from typing import Protocol


class PolicyAdapter(Protocol):
    """Minimal policy adapter surface reserved for later phases."""

    policy_type: str
