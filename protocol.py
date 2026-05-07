"""Wire protocol helpers for SO-101 remote teleoperation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


MSG_TYPE_ACTION_V1 = "action_v1"
MSG_TYPE_ACTION_ACK_V1 = "action_ack_v1"
EXPECTED_ACTION_LENGTH = 6
DEFAULT_ACTION_KEYS = (
    "shoulder_pan.pos",
    "shoulder_lift.pos",
    "elbow_flex.pos",
    "wrist_flex.pos",
    "wrist_roll.pos",
    "gripper.pos",
)


class ProtocolError(ValueError):
    """Raised when a UDP payload does not match the expected schema."""


@dataclass(slots=True, frozen=True)
class ActionMessage:
    """Validated teleoperation message sent from leader to follower."""

    seq: int
    sent_at_ns: int
    leader_id: str
    action: dict[str, float]
    msg_type: str = MSG_TYPE_ACTION_V1

    def to_dict(self) -> dict[str, Any]:
        return {
            "msg_type": self.msg_type,
            "seq": self.seq,
            "sent_at_ns": self.sent_at_ns,
            "leader_id": self.leader_id,
            "action": self.action,
        }


@dataclass(slots=True, frozen=True)
class AckMessage:
    """Validated acknowledgment message sent from follower to leader."""

    seq: int
    follower_id: str
    msg_type: str = MSG_TYPE_ACTION_ACK_V1

    def to_dict(self) -> dict[str, Any]:
        return {
            "msg_type": self.msg_type,
            "seq": self.seq,
            "follower_id": self.follower_id,
        }


def _normalize_action_values(action_values: Any, expected_len: int) -> list[float]:
    """Convert an action-like object into a validated list of floats."""

    if hasattr(action_values, "tolist"):
        action_values = action_values.tolist()

    try:
        values = [float(value) for value in action_values]
    except TypeError as exc:
        raise ProtocolError("Action must be an iterable of numeric values.") from exc
    except ValueError as exc:
        raise ProtocolError("Action values must be numeric.") from exc

    if len(values) != expected_len:
        raise ProtocolError(
            f"Expected action length {expected_len}, got {len(values)}."
        )

    return values


def normalize_action(
    action: Any,
    expected_len: int = EXPECTED_ACTION_LENGTH,
    action_keys: tuple[str, ...] = DEFAULT_ACTION_KEYS,
) -> dict[str, float]:
    """Convert an action-like object into a validated action dict.

    LeRobot SO-101 currently exposes teleop and robot actions as dictionaries
    keyed by joint names like ``shoulder_pan.pos``. For backward compatibility
    we also accept list-like payloads and map them to the canonical joint order.
    """

    if isinstance(action, dict):
        missing_keys = [key for key in action_keys if key not in action]
        if missing_keys:
            raise ProtocolError(
                f"Action dict missing expected keys: {', '.join(missing_keys)}."
            )
        normalized_values = _normalize_action_values(
            [action[key] for key in action_keys], expected_len=expected_len
        )
        return dict(zip(action_keys, normalized_values, strict=True))

    normalized_values = _normalize_action_values(action, expected_len=expected_len)
    return dict(zip(action_keys, normalized_values, strict=True))


def encode_action_message(message: ActionMessage) -> bytes:
    """Serialize an action message to compact JSON bytes."""

    return json.dumps(message.to_dict(), separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


def encode_ack_message(message: AckMessage) -> bytes:
    """Serialize an acknowledgment message to compact JSON bytes."""

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


def decode_ack_message(payload: bytes) -> AckMessage:
    """Deserialize and validate a UDP acknowledgment message."""

    try:
        raw = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("Payload is not valid UTF-8 JSON.") from exc

    if not isinstance(raw, dict):
        raise ProtocolError("Payload root must be a JSON object.")

    msg_type = raw.get("msg_type")
    if msg_type != MSG_TYPE_ACTION_ACK_V1:
        raise ProtocolError(f"Unsupported ack msg_type: {msg_type!r}.")

    seq = raw.get("seq")
    follower_id = raw.get("follower_id")

    if not isinstance(seq, int) or seq < 0:
        raise ProtocolError("Field 'seq' must be a non-negative integer.")
    if not isinstance(follower_id, str) or not follower_id:
        raise ProtocolError("Field 'follower_id' must be a non-empty string.")

    return AckMessage(msg_type=msg_type, seq=seq, follower_id=follower_id)
