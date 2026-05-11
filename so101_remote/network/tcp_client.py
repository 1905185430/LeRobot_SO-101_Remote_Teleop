"""Small TCP client helper for observation/action exchange."""

from __future__ import annotations

import socket
from types import TracebackType
from typing import Any, Mapping

from .protocol import MSG_ACTION, ProtocolError, recv_message, send_message


class TcpClient:
    """Connect to a policy/teleop server and exchange protocol messages."""

    def __init__(
        self,
        host: str,
        port: int,
        *,
        timeout_s: float = 1.0,
        max_packet_size: int = 16 * 1024 * 1024,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout_s = timeout_s
        self.max_packet_size = max_packet_size
        self.sock: socket.socket | None = None

    def connect(self) -> None:
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout_s)
        self.sock.settimeout(self.timeout_s)

    def close(self) -> None:
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def request_action(self, observation: Mapping[str, Any]) -> dict[str, Any]:
        """Send one observation and receive one action."""
        if self.sock is None:
            raise RuntimeError("TCP client is not connected.")
        send_message(self.sock, observation, max_size=self.max_packet_size)
        response = recv_message(self.sock, max_size=self.max_packet_size)
        if response.get("type") != MSG_ACTION:
            raise ProtocolError(f"Expected ACTION response, got {response.get('type')!r}.")
        return response

    def __enter__(self) -> TcpClient:
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
