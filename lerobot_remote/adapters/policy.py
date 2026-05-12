"""Policy adapter boundary for model integrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class PolicyAdapter(Protocol):
    """Minimal policy adapter surface used by runtime orchestration."""

    policy_type: str

    def load(self) -> None:
        """Load model resources."""

    def infer_action(self, observation: dict[str, object]) -> object:
        """Infer one action from an observation."""


@dataclass
class UnsupportedPolicyAdapter:
    """Placeholder for future policy/model backends."""

    policy_type: str = "unsupported"

    def load(self) -> None:
        self._raise()

    def infer_action(self, observation: dict[str, object]) -> object:
        self._raise()

    def _raise(self) -> None:
        raise NotImplementedError(f"No policy backend is implemented for {self.policy_type}.")


@dataclass
class PISeriesPolicyPlaceholder(UnsupportedPolicyAdapter):
    """Explicit placeholder for future PI-series support."""

    policy_type: str = "pi-series"

    def _raise(self) -> None:
        raise NotImplementedError("PI-series policy support is a placeholder.")
