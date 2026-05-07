"""Leader-side UDP sender for LeRobot SO-101 teleoperation."""

from __future__ import annotations

import argparse
import logging
import socket
import time
from typing import Any

from logging_utils import configure_logging, get_logger
from protocol import ActionMessage, ProtocolError, encode_action_message, normalize_action


DEFAULT_HZ = 50.0
DEFAULT_UDP_PORT = 5005


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
        sock: socket.socket | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.leader_device = leader_device
        self.target = (follower_ip, udp_port)
        self.leader_id = leader_id
        self.period_s = 1.0 / hz
        self.sock = sock or socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.logger = logger or get_logger("leader_sender")
        self.seq = 0

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
        return message

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
