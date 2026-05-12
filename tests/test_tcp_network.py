from __future__ import annotations

import socket
import threading
import time
import unittest

from lerobot_remote.network.protocol import (
    HEADER_SIZE,
    MSG_ACTION,
    MSG_OBSERVATION,
    ProtocolError,
    decode_payload,
    encode_message,
    make_action_message,
    make_observation_message,
    recv_message,
    send_message,
)
from lerobot_remote.network.tcp_client import TcpClient
from lerobot_remote.network.tcp_server import TcpServer, mirror_joint_action


JOINTS = {
    "shoulder_pan.pos": 0.1,
    "shoulder_lift.pos": -0.2,
    "elbow_flex.pos": 0.3,
    "wrist_flex.pos": 0.4,
    "wrist_roll.pos": -0.5,
    "gripper.pos": 0.6,
}


class TcpProtocolTests(unittest.TestCase):
    def test_encode_message_adds_4_byte_length_header(self) -> None:
        message = make_action_message(frame_id=1, timestamp_ns=2, action=JOINTS)

        encoded = encode_message(message)

        payload_size = int.from_bytes(encoded[:HEADER_SIZE], "big")
        self.assertEqual(payload_size, len(encoded) - HEADER_SIZE)
        self.assertEqual(decode_payload(encoded[HEADER_SIZE:])["type"], MSG_ACTION)

    def test_invalid_type_is_rejected(self) -> None:
        with self.assertRaisesRegex(ProtocolError, "Unsupported message type"):
            encode_message({"type": "WRONG"})

    def test_max_size_is_enforced(self) -> None:
        message = make_action_message(frame_id=1, timestamp_ns=2, action=JOINTS)

        with self.assertRaisesRegex(ProtocolError, "exceeds max size"):
            encode_message(message, max_size=1)

    def test_socketpair_send_and_receive(self) -> None:
        left, right = socket.socketpair()
        self.addCleanup(left.close)
        self.addCleanup(right.close)
        message = make_observation_message(
            frame_id=3,
            timestamp_ns=4,
            robot_type="so101_follower",
            joint_positions=JOINTS,
        )

        send_message(left, message)

        self.assertEqual(recv_message(right), message)


class TcpRoundTripTests(unittest.TestCase):
    def test_client_server_mock_observation_action_roundtrip(self) -> None:
        bind_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        bind_sock.bind(("127.0.0.1", 0))
        host, port = bind_sock.getsockname()
        bind_sock.close()

        server = TcpServer(host, port, mirror_joint_action, timeout_s=2.0)
        server_result: dict[str, object] = {}
        server_error: list[BaseException] = []

        def run_server() -> None:
            try:
                server_result.update(server.serve_once())
            except BaseException as exc:  # pragma: no cover - surfaced below
                server_error.append(exc)

        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        time.sleep(0.02)

        observation = make_observation_message(
            frame_id=9,
            timestamp_ns=10,
            robot_type="so101_follower",
            joint_positions=JOINTS,
        )
        with TcpClient(host, port, timeout_s=2.0) as client:
            action = client.request_action(observation)

        thread.join(timeout=2.0)
        self.assertFalse(server_error)
        self.assertEqual(action["type"], MSG_ACTION)
        self.assertEqual(action["frame_id"], 9)
        self.assertEqual(action["action"], JOINTS)
        self.assertEqual(server_result["type"], MSG_ACTION)

    def test_client_rejects_non_action_response(self) -> None:
        left, right = socket.socketpair()
        self.addCleanup(left.close)
        self.addCleanup(right.close)
        client = TcpClient("127.0.0.1", 1)
        client.sock = left
        observation = make_observation_message(
            frame_id=1,
            timestamp_ns=2,
            robot_type="so101_follower",
            joint_positions=JOINTS,
        )

        def respond_wrong_type() -> None:
            recv_message(right)
            send_message(right, {"type": MSG_OBSERVATION})

        thread = threading.Thread(target=respond_wrong_type, daemon=True)
        thread.start()

        with self.assertRaisesRegex(ProtocolError, "Expected ACTION"):
            client.request_action(observation)


if __name__ == "__main__":
    unittest.main()
