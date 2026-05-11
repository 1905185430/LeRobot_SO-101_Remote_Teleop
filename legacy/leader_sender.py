"""Leader-side UDP sender for LeRobot SO-101 teleoperation."""

from __future__ import annotations

import argparse
import logging
import socket
import time
from typing import Any

from .logging_utils import configure_logging, get_logger
from .protocol import ActionMessage, ProtocolError, encode_action_message, normalize_action


DEFAULT_HZ = 50.0
DEFAULT_UDP_PORT = 5005
DEFAULT_RTT_LOG_INTERVAL_S = 1.0
MAX_PENDING_ACK_AGE_S = 5.0


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Value must be > 0.")
    return parsed


def udp_port_type(value: str) -> int:
    parsed = int(value)
    if not 1 <= parsed <= 65535:
        raise argparse.ArgumentTypeError("UDP port must be in [1, 65535].")
    return parsed


class LeaderSender:
    """Read local teleop actions and stream them over UDP."""

    def __init__(
        self,
        leader_device: Any,
        follower_ip: str,
        udp_port: int,
        leader_id: str,
        hz: float = DEFAULT_HZ,
        rtt_log_interval_s: float = DEFAULT_RTT_LOG_INTERVAL_S,
        sock: socket.socket | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.leader_device = leader_device
        self.target = (follower_ip, udp_port)
        self.leader_id = leader_id
        self.period_s = 1.0 / hz
        self.rtt_log_interval_s = rtt_log_interval_s
        self.sock = sock or socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.logger = logger or get_logger("leader_sender")
        self.seq = 0
        self.pending_send_times_ns: dict[int, int] = {}
        self.last_rtt_ms: float | None = None
        self.rtt_sample_count = 0
        self.rtt_sum_ms = 0.0
        self.rtt_min_ms = float("inf")
        self.rtt_max_ms = float("-inf")
        self.last_rtt_log_monotonic_s = time.monotonic()

        self.sock.setblocking(False)

    def build_message(self) -> ActionMessage:
        action = normalize_action(self.leader_device.get_action())
        message = ActionMessage(
            seq=self.seq,
            sent_at_ns=time.time_ns(),
            leader_id=self.leader_id,
            action=action,
        )
        self.seq += 1
        return message

    def send_once(self) -> ActionMessage:
        message = self.build_message()
        self.sock.sendto(encode_action_message(message), self.target)
        self.pending_send_times_ns[message.seq] = time.monotonic_ns()
        return message

    def handle_ack(self, payload: bytes) -> float | None:
        from .protocol import decode_ack_message

        ack = decode_ack_message(payload)
        send_time_ns = self.pending_send_times_ns.pop(ack.seq, None)
        if send_time_ns is None:
            return None

        rtt_ms = (time.monotonic_ns() - send_time_ns) / 1_000_000
        self.last_rtt_ms = rtt_ms
        self.rtt_sample_count += 1
        self.rtt_sum_ms += rtt_ms
        self.rtt_min_ms = min(self.rtt_min_ms, rtt_ms)
        self.rtt_max_ms = max(self.rtt_max_ms, rtt_ms)
        return rtt_ms

    def poll_acks(self) -> int:
        processed = 0
        while True:
            try:
                payload, _addr = self.sock.recvfrom(4096)
            except BlockingIOError:
                break

            try:
                if self.handle_ack(payload) is not None:
                    processed += 1
            except ProtocolError as exc:
                self.logger.warning("Dropped invalid ACK packet: %s", exc)

        return processed

    def prune_stale_pending_acks(self, now_ns: int | None = None) -> None:
        if now_ns is None:
            now_ns = time.monotonic_ns()

        cutoff_ns = now_ns - int(MAX_PENDING_ACK_AGE_S * 1_000_000_000)
        stale = [seq for seq, sent_ns in self.pending_send_times_ns.items() if sent_ns < cutoff_ns]
        for seq in stale:
            self.pending_send_times_ns.pop(seq, None)

    def maybe_log_rtt(self, now_monotonic_s: float | None = None) -> None:
        if self.rtt_sample_count == 0 or self.rtt_log_interval_s <= 0:
            return

        if now_monotonic_s is None:
            now_monotonic_s = time.monotonic()

        if now_monotonic_s - self.last_rtt_log_monotonic_s < self.rtt_log_interval_s:
            return

        avg_rtt_ms = self.rtt_sum_ms / self.rtt_sample_count
        self.logger.info(
            "RTT: latest=%.2f ms avg=%.2f ms min=%.2f ms max=%.2f ms samples=%s in_flight=%s",
            self.last_rtt_ms,
            avg_rtt_ms,
            self.rtt_min_ms,
            self.rtt_max_ms,
            self.rtt_sample_count,
            len(self.pending_send_times_ns),
        )
        self.last_rtt_log_monotonic_s = now_monotonic_s

    def run(self) -> int:
        self.logger.info(
            "Leader sender started: leader_id=%s follower_ip=%s udp_port=%s hz=%.2f",
            self.leader_id,
            self.target[0],
            self.target[1],
            1.0 / self.period_s,
        )
        next_tick = time.perf_counter()
        try:
            while True:
                self.send_once()
                self.poll_acks()
                self.prune_stale_pending_acks()
                self.maybe_log_rtt()
                next_tick += self.period_s
                sleep_s = next_tick - time.perf_counter()
                if sleep_s > 0:
                    time.sleep(sleep_s)
                else:
                    next_tick = time.perf_counter()
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received, shutting down leader sender.")
            return 0


def build_leader_device(port: str, leader_id: str) -> Any:
    try:
        from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig
    except ImportError as exc:
        raise RuntimeError(
            "Failed to import LeRobot SO101Leader. Install 'lerobot' on the leader machine."
        ) from exc

    config = SO101LeaderConfig(port=port, id=leader_id)
    device = SO101Leader(config)
    device.connect()
    return device


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--leader-port", required=True, help="Serial port for the SO-101 leader arm.")
    parser.add_argument("--leader-id", required=True, help="LeRobot calibration id for the leader arm.")
    parser.add_argument("--follower-ip", required=True, help="IPv4 address of the follower machine.")
    parser.add_argument(
        "--udp-port",
        type=udp_port_type,
        default=DEFAULT_UDP_PORT,
        help="UDP port on the follower machine.",
    )
    parser.add_argument("--hz", type=positive_float, default=DEFAULT_HZ, help="Control loop frequency.")
    parser.add_argument(
        "--rtt-log-interval",
        type=positive_float,
        default=DEFAULT_RTT_LOG_INTERVAL_S,
        help="Seconds between RTT log lines on the leader terminal.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging()
    logger = get_logger("leader_sender")

    leader_device = None
    try:
        leader_device = build_leader_device(args.leader_port, args.leader_id)
        logger.info(
            "Leader hardware connected: leader_port=%s leader_id=%s",
            args.leader_port,
            args.leader_id,
        )
        sender = LeaderSender(
            leader_device=leader_device,
            follower_ip=args.follower_ip,
            udp_port=args.udp_port,
            leader_id=args.leader_id,
            hz=args.hz,
            rtt_log_interval_s=args.rtt_log_interval,
            logger=logger,
        )
        return sender.run()
    except (OSError, RuntimeError, ProtocolError, ValueError) as exc:
        logger.exception("Leader sender failed to start or run: %s", exc)
        return 1
    finally:
        if leader_device is not None:
            try:
                leader_device.disconnect()
            except Exception:  # pragma: no cover - best effort cleanup
                logger.exception("Leader disconnect failed.")


if __name__ == "__main__":
    raise SystemExit(main())
