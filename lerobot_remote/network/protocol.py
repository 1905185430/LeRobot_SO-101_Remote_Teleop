"""Length-prefixed JSON protocol helpers for TCP transport."""

from __future__ import annotations

import json
import socket
import struct
from typing import Any, Mapping

HEADER_SIZE = 4
DEFAULT_MAX_PACKET_SIZE = 16 * 1024 * 1024

MSG_OBSERVATION = "OBSERVATION"
MSG_ACTION = "ACTION"
MSG_HEARTBEAT = "HEARTBEAT"
MSG_RESET = "RESET"
MSG_STOP = "STOP"
MSG_ERROR = "ERROR"
MSG_ACK = "ACK"

VALID_MESSAGE_TYPES = {
    MSG_OBSERVATION,
    MSG_ACTION,
    MSG_HEARTBEAT,
    MSG_RESET,
    MSG_STOP,
    MSG_ERROR,
    MSG_ACK,
}


class ProtocolError(ValueError):
    """Raised when a TCP protocol message is malformed."""


def encode_message(message: Mapping[str, Any], max_size: int = DEFAULT_MAX_PACKET_SIZE) -> bytes:
    """Encode one message as `[4-byte length][JSON payload]`."""
    _validate_message(message)
    payload = json.dumps(dict(message), separators=(",", ":"), sort_keys=True).encode("utf-8")
    if len(payload) > max_size:
        raise ProtocolError(f"Message payload exceeds max size: {len(payload)} > {max_size}.")
    return struct.pack("!I", len(payload)) + payload


def decode_payload(payload: bytes) -> dict[str, Any]:
    """Decode and validate one JSON payload without a length header."""
    try:
        raw = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("Payload is not valid UTF-8 JSON.") from exc
    if not isinstance(raw, dict):
        raise ProtocolError("Payload root must be a JSON object.")
    _validate_message(raw)
    return raw


def send_message(sock: socket.socket, message: Mapping[str, Any], max_size: int = DEFAULT_MAX_PACKET_SIZE) -> None:
    """Send one complete length-prefixed message."""
    sock.sendall(encode_message(message, max_size=max_size))


def recv_message(sock: socket.socket, max_size: int = DEFAULT_MAX_PACKET_SIZE) -> dict[str, Any]:
    """Receive one complete length-prefixed message."""
    header = _recv_exact(sock, HEADER_SIZE)
    if len(header) != HEADER_SIZE:
        raise ProtocolError("Connection closed before message header was received.")
    (payload_size,) = struct.unpack("!I", header)
    if payload_size <= 0:
        raise ProtocolError("Message payload size must be positive.")
    if payload_size > max_size:
        raise ProtocolError(f"Message payload exceeds max size: {payload_size} > {max_size}.")
    return decode_payload(_recv_exact(sock, payload_size))


def make_observation_message(
    *,
    frame_id: int,
    timestamp_ns: int,
    robot_type: str,
    joint_positions: Mapping[str, float],
    images: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build an OBSERVATION message."""
    return {
        "type": MSG_OBSERVATION,
        "frame_id": int(frame_id),
        "timestamp_ns": int(timestamp_ns),
        "robot_type": robot_type,
        "joint_positions": dict(joint_positions),
        "images": dict(images or {}),
    }


def make_action_message(
    *,
    frame_id: int,
    timestamp_ns: int,
    action: Mapping[str, float],
) -> dict[str, Any]:
    """Build an ACTION message."""
    return {
        "type": MSG_ACTION,
        "frame_id": int(frame_id),
        "timestamp_ns": int(timestamp_ns),
        "action": dict(action),
    }


def _recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _validate_message(message: Mapping[str, Any]) -> None:
    msg_type = message.get("type")
    if msg_type not in VALID_MESSAGE_TYPES:
        raise ProtocolError(
            f"Unsupported message type {msg_type!r}. Expected one of: "
            f"{', '.join(sorted(VALID_MESSAGE_TYPES))}."
        )
