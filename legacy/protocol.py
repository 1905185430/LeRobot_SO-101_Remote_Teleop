"""Wire protocol helpers for SO-101 remote teleoperation."""
# SO-101 远程遥操作的有线协议辅助工具——定义 UDP 消息格式、编解码和校验逻辑

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

# ======== 协议常量 ========
MSG_TYPE_ACTION_V1 = "action_v1"       # 动作消息类型标识（Leader → Follower）
MSG_TYPE_ACTION_ACK_V1 = "action_ack_v1"  # 动作确认消息类型标识（Follower → Leader）
EXPECTED_ACTION_LENGTH = 6              # SO-101 为 6 自由度机械臂：5个关节 + 1个夹爪
DEFAULT_ACTION_KEYS = (                 # 标准关节名称（与 LeRobot SO-101 一致）
    "shoulder_pan.pos",    # 肩部旋转
    "shoulder_lift.pos",   # 肩部抬升
    "elbow_flex.pos",      # 肘部弯曲
    "wrist_flex.pos",      # 腕部弯曲
    "wrist_roll.pos",      # 腕部旋转
    "gripper.pos",         # 夹爪开合
)


class ProtocolError(ValueError):
    """Raised when a UDP payload does not match the expected schema."""
    # 当 UDP 数据包不符合预期格式时抛出的异常


@dataclass(slots=True, frozen=True)
class ActionMessage:
    """Validated teleoperation message sent from leader to follower."""
    # 已校验的遥操作消息，由 Leader 端发往 Follower 端
    # 使用 frozen=True + slots=True 确保消息不可变且内存高效

    seq: int             # 单调递增的序列号，用于检测丢包和乱序
    sent_at_ns: int      # 发送时的纳秒级时间戳（用于计算网络延迟/RTT）
    leader_id: str       # Leader 臂的唯一标识
    action: dict[str, float]  # 6 关节目标位置（关节名 → 目标角度）
    msg_type: str = MSG_TYPE_ACTION_V1

    def to_dict(self) -> dict[str, Any]:
        """将动作消息序列化为 dict，准备 JSON 编码"""
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
    # 已校验的确认消息，由 Follower 端发回 Leader 端
    # Leader 通过 ACK 知道哪一帧已被 Follower 成功接收

    seq: int              # 对应已接收到的 ActionMessage 的序列号
    follower_id: str      # Follower 臂的唯一标识
    msg_type: str = MSG_TYPE_ACTION_ACK_V1

    def to_dict(self) -> dict[str, Any]:
        """将确认消息序列化为 dict，准备 JSON 编码"""
        return {
            "msg_type": self.msg_type,
            "seq": self.seq,
            "follower_id": self.follower_id,
        }


def _normalize_action_values(action_values: Any, expected_len: int) -> list[float]:
    """Convert an action-like object into a validated list of floats."""
    # 将任意形式的动作数据（list/ndarray/dict.values）统一转为浮点数列表并校验

    # 如果数据带有 .tolist() 方法（如 numpy 数组），先转换为 Python 列表
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
    # 将任意形式的动作数据转为标准化的 {关节名: 角度值} dict
    # 同时兼容 dict 格式（首选）和 list/array 格式（按标准关节顺序映射）

    if isinstance(action, dict):
        # dict 格式：检查是否包含所有必需的关节键名
        missing_keys = [key for key in action_keys if key not in action]
        if missing_keys:
            raise ProtocolError(
                f"Action dict missing expected keys: {', '.join(missing_keys)}."
            )
        normalized_values = _normalize_action_values(
            [action[key] for key in action_keys], expected_len=expected_len
        )
        return dict(zip(action_keys, normalized_values, strict=True))

    # list/array 格式：按 DEFAULT_ACTION_KEYS 的顺序映射
    normalized_values = _normalize_action_values(action, expected_len=expected_len)
    return dict(zip(action_keys, normalized_values, strict=True))


def encode_action_message(message: ActionMessage) -> bytes:
    """Serialize an action message to compact JSON bytes."""
    # 将动作消息序列化为紧凑 JSON → UTF-8 字节（无多余空格，适合 UDP 传输）
    return json.dumps(message.to_dict(), separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


def encode_ack_message(message: AckMessage) -> bytes:
    """Serialize an acknowledgment message to compact JSON bytes."""
    # 将确认消息序列化为紧凑 JSON → UTF-8 字节
    return json.dumps(message.to_dict(), separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


def decode_action_message(payload: bytes, expected_len: int = EXPECTED_ACTION_LENGTH) -> ActionMessage:
    """Deserialize and validate a UDP action message."""
    # 从 UDP 字节流中反序列化并校验动作消息，分三层校验：
    # 1. UTF-8 / JSON 格式校验
    # 2. 消息类型和字段类型校验
    # 3. 动作值的归一化和长度校验

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

    # 逐字段校验类型和合法性
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
    # 从 UDP 字节流中反序列化并校验确认消息

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
