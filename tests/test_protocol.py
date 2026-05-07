from __future__ import annotations

import unittest

from protocol import (
    AckMessage,
    ActionMessage,
    DEFAULT_ACTION_KEYS,
    MSG_TYPE_ACTION_V1,
    MSG_TYPE_ACTION_ACK_V1,
    ProtocolError,
    decode_ack_message,
    decode_action_message,
    encode_ack_message,
    encode_action_message,
    normalize_action,
)


class ProtocolTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        message = ActionMessage(
            seq=3,
            sent_at_ns=123456789,
            leader_id="leader_arm",
            action={
                "shoulder_pan.pos": 0.0,
                "shoulder_lift.pos": 1.0,
                "elbow_flex.pos": 2.0,
                "wrist_flex.pos": 3.0,
                "wrist_roll.pos": 4.0,
                "gripper.pos": 5.0,
            },
        )

        decoded = decode_action_message(encode_action_message(message))

        self.assertEqual(decoded, message)

    def test_normalize_action_uses_tolist(self) -> None:
        class FakeArray:
            def tolist(self) -> list[float]:
                return [1, 2, 3, 4, 5, 6]

        self.assertEqual(
            normalize_action(FakeArray()),
            dict(zip(DEFAULT_ACTION_KEYS, [1.0, 2.0, 3.0, 4.0, 5.0, 6.0], strict=True)),
        )

    def test_normalize_action_preserves_joint_names(self) -> None:
        action = {
            "shoulder_pan.pos": 1,
            "shoulder_lift.pos": 2,
            "elbow_flex.pos": 3,
            "wrist_flex.pos": 4,
            "wrist_roll.pos": 5,
            "gripper.pos": 6,
        }

        self.assertEqual(
            normalize_action(action),
            dict(zip(DEFAULT_ACTION_KEYS, [1.0, 2.0, 3.0, 4.0, 5.0, 6.0], strict=True)),
        )

    def test_invalid_json_is_rejected(self) -> None:
        with self.assertRaises(ProtocolError):
            decode_action_message(b"{not-json}")

    def test_wrong_msg_type_is_rejected(self) -> None:
        payload = (
            b'{"msg_type":"unexpected","seq":1,"sent_at_ns":2,'
            b'"leader_id":"leader","action":{"shoulder_pan.pos":0,"shoulder_lift.pos":1,'
            b'"elbow_flex.pos":2,"wrist_flex.pos":3,"wrist_roll.pos":4,"gripper.pos":5}}'
        )

        with self.assertRaises(ProtocolError):
            decode_action_message(payload)

    def test_missing_field_is_rejected(self) -> None:
        payload = b'{"msg_type":"action_v1","seq":1,"sent_at_ns":2,"leader_id":"leader"}'

        with self.assertRaises(ProtocolError):
            decode_action_message(payload)

    def test_wrong_action_length_is_rejected(self) -> None:
        payload = (
            b'{"msg_type":"action_v1","seq":1,"sent_at_ns":2,'
            b'"leader_id":"leader","action":[0,1]}'
        )

        with self.assertRaises(ProtocolError):
            decode_action_message(payload)

    def test_message_type_constant_matches_wire_contract(self) -> None:
        self.assertEqual(MSG_TYPE_ACTION_V1, "action_v1")

    def test_ack_round_trip(self) -> None:
        ack = AckMessage(seq=7, follower_id="follower_arm")

        decoded = decode_ack_message(encode_ack_message(ack))

        self.assertEqual(decoded, ack)

    def test_wrong_ack_type_is_rejected(self) -> None:
        payload = b'{"msg_type":"wrong","seq":1,"follower_id":"follower_arm"}'

        with self.assertRaises(ProtocolError):
            decode_ack_message(payload)

    def test_ack_message_type_constant_matches_wire_contract(self) -> None:
        self.assertEqual(MSG_TYPE_ACTION_ACK_V1, "action_ack_v1")


if __name__ == "__main__":
    unittest.main()
