"""Small one-client TCP server helper for mock policy exchange."""

from __future__ import annotations

from collections.abc import Callable
import socket
from typing import Any, Mapping

from .protocol import MSG_OBSERVATION, ProtocolError, recv_message, send_message

ObservationHandler = Callable[[dict[str, Any]], Mapping[str, Any]]


class TcpServer:
    """Serve length-prefixed protocol messages to one client at a time."""

    def __init__(
        self,
        host: str,
        port: int,
        handler: ObservationHandler,
        *,
        timeout_s: float = 1.0,
        max_packet_size: int = 16 * 1024 * 1024,
    ) -> None:
        self.host = host
        self.port = port
        self.handler = handler
        self.timeout_s = timeout_s
        self.max_packet_size = max_packet_size

    def serve_once(self) -> dict[str, Any]:
        """Accept one client, process one observation, and return the response."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((self.host, self.port))
            server_sock.listen(1)
            server_sock.settimeout(self.timeout_s)
            conn, _addr = server_sock.accept()
            with conn:
                conn.settimeout(self.timeout_s)
                observation = recv_message(conn, max_size=self.max_packet_size)
                if observation.get("type") != MSG_OBSERVATION:
                    raise ProtocolError(
                        f"Expected OBSERVATION request, got {observation.get('type')!r}."
                    )
                response = dict(self.handler(observation))
                send_message(conn, response, max_size=self.max_packet_size)
                return response


def mirror_joint_action(observation: Mapping[str, Any]) -> dict[str, Any]:
    """Mock policy handler that mirrors joint positions into an action."""
    joints = observation.get("joint_positions", {})
    if not isinstance(joints, Mapping):
        raise ProtocolError("OBSERVATION joint_positions must be a mapping.")
    return {
        "type": "ACTION",
        "frame_id": observation.get("frame_id", 0),
        "timestamp_ns": observation.get("timestamp_ns", 0),
        "action": {str(key): float(value) for key, value in joints.items()},
    }
