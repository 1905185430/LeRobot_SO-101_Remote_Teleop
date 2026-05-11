"""LeRobot async inference policy server runtime helpers."""

from __future__ import annotations

from pathlib import Path

from .config import HOST, POLICY_DEVICE, POLICY_TYPE, PORT, PRETRAINED_NAME_OR_PATH
from .recorder import build_run_metadata


def server_settings() -> dict[str, object]:
    """Return resolved policy server settings for logs and metadata."""
    return {"host": HOST, "port": PORT, "endpoint": f"{HOST}:{PORT}"}


def build_server_metadata(run_dir: str | Path) -> dict[str, object]:
    """Build reproducibility metadata for a policy server run."""
    return build_run_metadata(
        role="policy-server",
        server=server_settings(),
        policy={
            "type": POLICY_TYPE,
            "pretrained_name_or_path": PRETRAINED_NAME_OR_PATH,
            "device": POLICY_DEVICE,
        },
        extra={"resolved_settings": server_settings(), "run_dir": str(run_dir)},
    )


def build_server_config():
    """Build the official LeRobot policy server config object."""
    PolicyServerConfig, _serve = _load_server_api()
    return PolicyServerConfig(host=HOST, port=PORT)


def main() -> int:
    """Start the LeRobot async inference policy server."""
    _PolicyServerConfig, serve = _load_server_api()
    config = build_server_config()
    serve(config)
    return 0


def _load_server_api():
    """Load LeRobot server APIs lazily so imports remain test-friendly."""
    try:
        from lerobot.async_inference.configs import PolicyServerConfig
        from lerobot.async_inference.policy_server import serve
    except ImportError as exc:
        raise RuntimeError(
            "LeRobot async inference is not available. Install lerobot on this machine "
            "before running policy_server.py."
        ) from exc

    return PolicyServerConfig, serve
