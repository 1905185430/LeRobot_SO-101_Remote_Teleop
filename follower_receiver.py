"""Follower-side UDP receiver for LeRobot SO-101 teleoperation."""

from __future__ import annotations

import argparse
import logging
import socket
import time
from typing import Any

from logging_utils import configure_logging, get_logger
from protocol import ActionMessage, ProtocolError, decode_action_message


DEFAULT_BIND_IP = "0.0.0.0"
DEFAULT_HZ = 50.0
DEFAULT_TIMEOUT_MS = 200
DEFAULT_UDP_PORT = 5005
MAX_UDP_PACKET_SIZE = 4096


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Value must be > 0.")
    return parsed


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Value must be > 0.")
    return parsed


def udp_port_type(value: str) -> int:
    parsed = int(value)
    if not 1 <= parsed <= 65535:
        raise argparse.ArgumentTypeError("UDP port must be in [1, 65535].")
    return parsed


class FollowerReceiver:
    """Receive network actions and drive a local follower arm safely."""

    def __init__(
        self,
        follower_robot: Any,
        sock: socket.socket,
        hz: float = DEFAULT_HZ,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        logger: logging.Logger | None = None,
    ) -> None:
        self.follower_robot = follower_robot
        self.sock = sock
        self.period_s = 1.0 / hz
        self.timeout_ns = timeout_ms * 1_000_000
        self.logger = logger or get_logger("follower_receiver")

        self.last_valid_action: list[float] | None = None
        self.last_packet_monotonic_ns: int | None = None
        self.last_seq: int | None = None
        self.first_packet_seen = False
        self.timeout_active = False
        self.decode_error_count = 0

        self.sock.setblocking(False)

    def handle_datagram(self, payload: bytes, received_at_ns: int | None = None) -> ActionMessage:
        message = decode_action_message(payload)
        if self.last_seq is not None and message.seq <= self.last_seq:
            raise ProtocolError(
                f"Out-of-order or duplicate packet: seq={message.seq}, last_seq={self.last_seq}."
            )

        if received_at_ns is None:
            received_at_ns = time.monotonic_ns()

        self.last_valid_action = message.action
        self.last_packet_monotonic_ns = received_at_ns
        self.last_seq = message.seq

        if not self.first_packet_seen:
            self.logger.info(
                "First control packet received: leader_id=%s seq=%s",
                message.leader_id,
                message.seq,
            )
            self.first_packet_seen = True

        if self.timeout_active:
            self.timeout_active = False
            self.logger.info("Control stream recovered at seq=%s.", message.seq)

        return message

    def poll_network(self) -> int:
        processed = 0
        while True:
            try:
                payload, _addr = self.sock.recvfrom(MAX_UDP_PACKET_SIZE)
            except BlockingIOError:
                break

            try:
                self.handle_datagram(payload)
                processed += 1
            except ProtocolError as exc:
                self.decode_error_count += 1
                if self.decode_error_count == 1 or self.decode_error_count % 10 == 0:
                    self.logger.warning(
                        "Dropped invalid control packet (%s total): %s",
                        self.decode_error_count,
                        exc,
                    )

        return processed

    def get_current_action(self, now_ns: int | None = None) -> list[float] | None:
        if self.last_valid_action is None:
            return None

        if now_ns is None:
            now_ns = time.monotonic_ns()

        if self.last_packet_monotonic_ns is None:
            return self.last_valid_action

        if now_ns - self.last_packet_monotonic_ns > self.timeout_ns:
            if not self.timeout_active:
                self.timeout_active = True
                self.logger.error(
                    "Control stream timeout after %.1f ms; holding last known position.",
                    self.timeout_ns / 1_000_000,
                )
            return self.last_valid_action

        return self.last_valid_action

    def control_step(self, now_ns: int | None = None) -> bool:
        action = self.get_current_action(now_ns=now_ns)
        if action is None:
            return False

        self.follower_robot.send_action(action)
        return True

    def run(self) -> int:
        self.logger.info(
            "Follower receiver started: hz=%.2f timeout_ms=%.1f",
            1.0 / self.period_s,
            self.timeout_ns / 1_000_000,
        )
        next_tick = time.perf_counter()
        try:
            while True:
                self.poll_network()
                self.control_step()
                next_tick += self.period_s
                sleep_s = next_tick - time.perf_counter()
                if sleep_s > 0:
                    time.sleep(sleep_s)
                else:
                    next_tick = time.perf_counter()
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received, shutting down follower receiver.")
            return 0


def build_follower_robot(port: str, follower_id: str) -> Any:
    try:
        from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig
    except ImportError as exc:
        raise RuntimeError(
            "Failed to import LeRobot SO101Follower. Install 'lerobot' on the follower machine."
        ) from exc

    config = SO101FollowerConfig(port=port, id=follower_id)
    robot = SO101Follower(config)
    robot.connect()
    return robot


def build_server_socket(bind_ip: str, udp_port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((bind_ip, udp_port))
    return sock


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--follower-port", required=True, help="Serial port for the SO-101 follower arm.")
    parser.add_argument("--follower-id", required=True, help="LeRobot calibration id for the follower arm.")
    parser.add_argument("--bind-ip", default=DEFAULT_BIND_IP, help="UDP bind address.")
    parser.add_argument("--udp-port", type=udp_port_type, default=DEFAULT_UDP_PORT, help="UDP listen port.")
    parser.add_argument("--hz", type=positive_float, default=DEFAULT_HZ, help="Control loop frequency.")
    parser.add_argument(
        "--timeout-ms",
        type=positive_int,
        default=DEFAULT_TIMEOUT_MS,
        help="Timeout before holding the last known position.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging()
    logger = get_logger("follower_receiver")

    follower_robot = None
    sock = None
    try:
        sock = build_server_socket(args.bind_ip, args.udp_port)
        logger.info(
            "Follower UDP socket bound: bind_ip=%s udp_port=%s",
            args.bind_ip,
            args.udp_port,
        )
        follower_robot = build_follower_robot(args.follower_port, args.follower_id)
        logger.info(
            "Follower hardware connected: follower_port=%s follower_id=%s",
            args.follower_port,
            args.follower_id,
        )
        receiver = FollowerReceiver(
            follower_robot=follower_robot,
            sock=sock,
            hz=args.hz,
            timeout_ms=args.timeout_ms,
            logger=logger,
        )
        return receiver.run()
    except (OSError, RuntimeError, ValueError) as exc:
        logger.exception("Follower receiver failed to start or run: %s", exc)
        return 1
    finally:
        if follower_robot is not None:
            try:
                follower_robot.disconnect()
            except Exception:  # pragma: no cover - best effort cleanup
                logger.exception("Follower disconnect failed.")
        if sock is not None:
            sock.close()


if __name__ == "__main__":
    raise SystemExit(main())
