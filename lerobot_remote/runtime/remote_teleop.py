"""Compatibility imports for TCP teleoperation runtimes.

New code should import from :mod:`lerobot_remote.runtime.teleoperation`.
"""

from __future__ import annotations

from .teleoperation import run_tcp_teleop_follower_server, run_tcp_teleop_leader_client

__all__ = [
    "run_tcp_teleop_follower_server",
    "run_tcp_teleop_leader_client",
]
