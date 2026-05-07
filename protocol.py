"""Wire protocol helpers for SO-101 remote teleoperation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


MSG_TYPE_ACTION_V1 = "action_v1"
EXPECTED_ACTION_LENGTH = 6


class ProtocolError(ValueError):
    """Raised when a UDP payload does not match the expected schema."""


@dataclass(slots=True, frozen=True)
class ActionMessage:
    """Validated teleoperation message sent from leader to follower."""

    seq: int
    sent_at_ns: int
    leader_id: str
    action: list[float]
    msg_type: str = MSG_TYPE_ACTION_V1

    def to_dict(self) -> dict[str, Any]:
        return {
            "msg_type": self.msg_type,
            "seq": self.seq,
            "sent_at_ns": self.sent_at_ns,
            "leader_id": self.leader_id,
            "action": self.action,
        }


def normalize_action(action: Any, expected_len: int = EXPECTED_ACTION_LENGTH) -> list[float]:
    """Convert an action-like object into a validated list of floats."""

    if hasattr(action, "tolist"):
        action = action.tolist()

    try:
        values = [float(value) for value in action]
    except TypeError as exc:
        raise ProtocolError("Action must be an iterable of numeric values.") from exc
    except ValueError as exc:
        raise ProtocolError("Action values must be numeric.") from exc

    if len(values) != expected_len:
        raise ProtocolError(
            f"Expected action length {expected_len}, got {len(values)}."
        )

    return values


def encode_action_message(message: ActionMessage) -> bytes:
    """Serialize an action message to compact JSON bytes."""

    return json.dumps(message.to_dict(), separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


def decode_action_message(payload: bytes, expected_len: int = EXPECTED_ACTION_LENGTH) -> ActionMessage:
    """Deserialize and validate a UDP action message."""

    try:
        raw = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("Payload is not valid UTF-8 JSON.") from exc

    if not isinstance(raw, dict):
        raise ProtocolError("Payload root must be a JSON object.")

    msg_type = raw.get("msg_type")
    if msg_type != MSG_TYPE_ACTION_V1:
        raise ProtocolError(f"Unsupported msg_type: {msg_type!r}.")

    seq = raw.get("seq")
    sent_at_ns = raw.get("sent_at_ns")
    leader_id = raw.get("leader_id")
    action = raw.get("action")

    if not isinstance(seq, int) or seq < 0:
        raise ProtocolError("Field 'seq' must be a non-negative integer.")
    if not isinstance(sent_at_ns, int) or sent_at_ns < 0:
        raise ProtocolError("Field 'sent_at_ns' must be a non-negative integer.")
    if not isinstance(leader_id, str) or not leader_id:
        raise ProtocolError("Field 'leader_id' must be a non-empty string.")

    return ActionMessage(
        msg_type=msg_type,
        seq=seq,
        sent_at_ns=sent_at_ns,
        leader_id=leader_id,
        action=normalize_action(action, expected_len=expected_len),
    )
