"""LeRobot async inference policy server runtime helpers."""

from __future__ import annotations

from .config import HOST, PORT


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
