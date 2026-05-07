from __future__ import annotations

import logging
import socket
import time
import unittest
from unittest import mock

from follower_receiver import FollowerReceiver
from leader_sender import LeaderSender
from protocol import ActionMessage, DEFAULT_ACTION_KEYS, encode_action_message


class DummyLeader:
    def __init__(self, actions: list[dict[str, float] | list[float]]) -> None:
        self._actions = list(actions)

    def get_action(self) -> dict[str, float] | list[float]:
        return self._actions.pop(0)


class DummyRobot:
    def __init__(self) -> None:
        self.sent_actions: list[dict[str, float]] = []

    def send_action(self, action: dict[str, float]) -> None:
        self.sent_actions.append(dict(action))


def make_action(values: list[float]) -> dict[str, float]:
    return dict(zip(DEFAULT_ACTION_KEYS, values, strict=True))


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
            leader_device=DummyLeader([make_action([0, 1, 2, 3, 4, 5])]),
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
                    make_action([0, 1, 2, 3, 4, 5]),
                    make_action([5, 4, 3, 2, 1, 0]),
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
                action=make_action([0, 1, 2, 3, 4, 5]),
            )
        )
        client.sendto(payload, target)

        self.assertEqual(receiver.poll_network(), 1)
        self.assertTrue(receiver.control_step())
        self.assertEqual(robot.sent_actions[-1], make_action([0, 1, 2, 3, 4, 5]))

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
                    action=make_action([1, 1, 1, 1, 1, 1]),
                )
            ),
            received_at_ns=base_ns,
            received_wall_time_ns=1_000_000_000,
        )

        for step in range(1, 6):
            now_ns = base_ns + step * 20_000_000
            self.assertTrue(receiver.control_step(now_ns=now_ns))

        self.assertEqual(len(robot.sent_actions), 5)
        self.assertTrue(all(action == make_action([1, 1, 1, 1, 1, 1]) for action in robot.sent_actions))

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
                    sent_at_ns=500_000_000,
                    leader_id="leader_arm",
                    action=make_action([2, 2, 2, 2, 2, 2]),
                )
            ),
            received_at_ns=base_ns,
            received_wall_time_ns=700_000_000,
        )

        self.assertFalse(receiver.timeout_active)
        self.assertTrue(receiver.control_step(now_ns=base_ns + 250_000_000))
        self.assertTrue(receiver.timeout_active)
        self.assertEqual(robot.sent_actions[-1], make_action([2, 2, 2, 2, 2, 2]))

        receiver.handle_datagram(
            encode_action_message(
                ActionMessage(
                    seq=2,
                    sent_at_ns=800_000_000,
                    leader_id="leader_arm",
                    action=make_action([3, 3, 3, 3, 3, 3]),
                )
            ),
            received_at_ns=base_ns + 260_000_000,
            received_wall_time_ns=950_000_000,
        )

        self.assertFalse(receiver.timeout_active)
        self.assertTrue(receiver.control_step(now_ns=base_ns + 270_000_000))
        self.assertEqual(robot.sent_actions[-1], make_action([3, 3, 3, 3, 3, 3]))

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

    def test_latency_stats_are_tracked_and_logged(self) -> None:
        server, _target, client = make_udp_pair()
        self.addCleanup(server.close)
        self.addCleanup(client.close)

        logger = logging.getLogger("test.follower.latency")
        receiver = FollowerReceiver(
            follower_robot=DummyRobot(),
            sock=server,
            latency_log_interval_s=1.0,
            logger=logger,
        )

        receiver.handle_datagram(
            encode_action_message(
                ActionMessage(
                    seq=0,
                    sent_at_ns=1_000_000_000,
                    leader_id="leader_arm",
                    action=make_action([0, 1, 2, 3, 4, 5]),
                )
            ),
            received_at_ns=2_000_000_000,
            received_wall_time_ns=1_012_000_000,
        )
        receiver.handle_datagram(
            encode_action_message(
                ActionMessage(
                    seq=1,
                    sent_at_ns=1_100_000_000,
                    leader_id="leader_arm",
                    action=make_action([0, 1, 2, 3, 4, 5]),
                )
            ),
            received_at_ns=2_100_000_000,
            received_wall_time_ns=1_118_000_000,
        )

        self.assertAlmostEqual(receiver.last_packet_latency_ms or 0.0, 18.0)
        self.assertAlmostEqual(receiver.latency_sum_ms, 30.0)
        self.assertEqual(receiver.latency_sample_count, 2)
        self.assertAlmostEqual(receiver.latency_max_ms, 18.0)

        with mock.patch.object(logger, "info") as info_mock:
            receiver.maybe_log_latency(
                now_monotonic_s=receiver.last_latency_log_monotonic_s + 1.5,
                now_monotonic_ns=2_150_000_000,
            )

        info_mock.assert_called_once()
        logged_args = info_mock.call_args[0]
        self.assertEqual(
            logged_args[0],
            "Latency: latest=%.2f ms avg=%.2f ms max=%.2f ms samples=%s stream_age=%.2f ms",
        )
        self.assertEqual(logged_args[1:5], (18.0, 15.0, 18.0, 2))
        self.assertAlmostEqual(logged_args[5], 50.0)


if __name__ == "__main__":
    unittest.main()
