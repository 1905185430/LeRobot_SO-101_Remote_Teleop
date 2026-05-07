from __future__ import annotations

import logging
import socket
import time
import unittest

from follower_receiver import FollowerReceiver
from leader_sender import LeaderSender
from protocol import ActionMessage, encode_action_message


class DummyLeader:
    def __init__(self, actions: list[list[float]]) -> None:
        self._actions = list(actions)

    def get_action(self) -> list[float]:
        return self._actions.pop(0)


class DummyRobot:
    def __init__(self) -> None:
        self.sent_actions: list[list[float]] = []

    def send_action(self, action: list[float]) -> None:
        self.sent_actions.append(list(action))


def make_udp_pair() -> tuple[socket.socket, tuple[str, int], socket.socket]:
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(("127.0.0.1", 0))
    host, port = server.getsockname()

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return server, (host, port), client


class LeaderSenderTests(unittest.TestCase):
    def test_send_once_sends_udp_packet(self) -> None:
        server, target, client = make_udp_pair()
        self.addCleanup(server.close)
        self.addCleanup(client.close)

        sender = LeaderSender(
            leader_device=DummyLeader([[0, 1, 2, 3, 4, 5]]),
            follower_ip=target[0],
            udp_port=target[1],
            leader_id="leader_arm",
            sock=client,
            logger=logging.getLogger("test.leader"),
        )

        sent = sender.send_once()
        payload, _addr = server.recvfrom(4096)

        self.assertEqual(sent.seq, 0)
        self.assertEqual(sender.seq, 1)
        self.assertIn(b'"msg_type":"action_v1"', payload)

    def test_sequence_is_monotonic(self) -> None:
        server, target, client = make_udp_pair()
        self.addCleanup(server.close)
        self.addCleanup(client.close)

        sender = LeaderSender(
            leader_device=DummyLeader(
                [
                    [0, 1, 2, 3, 4, 5],
                    [5, 4, 3, 2, 1, 0],
                ]
            ),
            follower_ip=target[0],
            udp_port=target[1],
            leader_id="leader_arm",
            sock=client,
            logger=logging.getLogger("test.leader"),
        )

        first = sender.send_once()
        second = sender.send_once()

        self.assertEqual((first.seq, second.seq), (0, 1))


class FollowerReceiverTests(unittest.TestCase):
    def test_receives_and_executes_action(self) -> None:
        server, target, client = make_udp_pair()
        self.addCleanup(server.close)
        self.addCleanup(client.close)

        robot = DummyRobot()
        receiver = FollowerReceiver(
            follower_robot=robot,
            sock=server,
            logger=logging.getLogger("test.follower"),
        )

        payload = encode_action_message(
            ActionMessage(
                seq=0,
                sent_at_ns=time.time_ns(),
                leader_id="leader_arm",
                action=[0, 1, 2, 3, 4, 5],
            )
        )
        client.sendto(payload, target)

        self.assertEqual(receiver.poll_network(), 1)
        self.assertTrue(receiver.control_step())
        self.assertEqual(robot.sent_actions[-1], [0.0, 1.0, 2.0, 3.0, 4.0, 5.0])

    def test_packet_loss_holds_last_action(self) -> None:
        server, _target, client = make_udp_pair()
        self.addCleanup(server.close)
        self.addCleanup(client.close)

        robot = DummyRobot()
        receiver = FollowerReceiver(
            follower_robot=robot,
            sock=server,
            timeout_ms=200,
            logger=logging.getLogger("test.follower"),
        )

        base_ns = time.monotonic_ns()
        receiver.handle_datagram(
            encode_action_message(
                ActionMessage(
                    seq=0,
                    sent_at_ns=time.time_ns(),
                    leader_id="leader_arm",
                    action=[1, 1, 1, 1, 1, 1],
                )
            ),
            received_at_ns=base_ns,
        )

        for step in range(1, 6):
            now_ns = base_ns + step * 20_000_000
            self.assertTrue(receiver.control_step(now_ns=now_ns))

        self.assertEqual(len(robot.sent_actions), 5)
        self.assertTrue(all(action == [1.0] * 6 for action in robot.sent_actions))

    def test_timeout_enters_hold_and_recovers(self) -> None:
        server, _target, client = make_udp_pair()
        self.addCleanup(server.close)
        self.addCleanup(client.close)

        robot = DummyRobot()
        receiver = FollowerReceiver(
            follower_robot=robot,
            sock=server,
            timeout_ms=200,
            logger=logging.getLogger("test.follower"),
        )

        base_ns = time.monotonic_ns()
        receiver.handle_datagram(
            encode_action_message(
                ActionMessage(
                    seq=1,
                    sent_at_ns=time.time_ns(),
                    leader_id="leader_arm",
                    action=[2, 2, 2, 2, 2, 2],
                )
            ),
            received_at_ns=base_ns,
        )

        self.assertFalse(receiver.timeout_active)
        self.assertTrue(receiver.control_step(now_ns=base_ns + 250_000_000))
        self.assertTrue(receiver.timeout_active)
        self.assertEqual(robot.sent_actions[-1], [2.0] * 6)

        receiver.handle_datagram(
            encode_action_message(
                ActionMessage(
                    seq=2,
                    sent_at_ns=time.time_ns(),
                    leader_id="leader_arm",
                    action=[3, 3, 3, 3, 3, 3],
                )
            ),
            received_at_ns=base_ns + 260_000_000,
        )

        self.assertFalse(receiver.timeout_active)
        self.assertTrue(receiver.control_step(now_ns=base_ns + 270_000_000))
        self.assertEqual(robot.sent_actions[-1], [3.0] * 6)

    def test_invalid_packets_are_counted(self) -> None:
        server, target, client = make_udp_pair()
        self.addCleanup(server.close)
        self.addCleanup(client.close)

        receiver = FollowerReceiver(
            follower_robot=DummyRobot(),
            sock=server,
            logger=logging.getLogger("test.follower"),
        )

        client.sendto(b"not-json", target)
        self.assertEqual(receiver.poll_network(), 0)

        self.assertEqual(receiver.decode_error_count, 1)


if __name__ == "__main__":
    unittest.main()
