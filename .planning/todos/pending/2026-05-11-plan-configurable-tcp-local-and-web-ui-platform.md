---
created: 2026-05-11T10:16:33.152Z
title: Plan configurable TCP local and web UI platform
area: planning
files:
  - .planning/ROADMAP.md
  - .planning/PROJECT.md
  - .planning/REQUIREMENTS.md
  - so101_remote/config.py
  - policy_server.py
  - robot_client.py
  - legacy/
---

## Problem

Future work needs to evolve the current SO-101 + SmolVLA experiment framework into a more configurable platform while still staying grounded in LeRobot. The desired baseline is:

- Support a local single-machine inference option that does not involve wireless networking.
- Keep the internal runtime based on the LeRobot framework.
- Use TCP for the two-host path, with both hosts on the same LAN.
- Keep a `client` Python program and a `server` Python program.
- Add a unified config entry point that selects model, robot arm type, operation mode, and task-specific settings.
- Support multiple selectable configs for different tasks.
- Make operation mode explicit, such as inference, teleoperation, or later modes.

The current v1 code intentionally keeps constants lightweight. That was appropriate for the first working path, but the next milestone needs a proper configuration and runtime-mode design before adding more robots, teleoperation modes, or model backends.

## Solution

TBD during the next milestone planning. Likely work:

- Design a config system that can load named task configs while preserving simple defaults.
- Define runtime modes such as `local-inference`, `tcp-inference`, `teleoperation`, and future modes.
- Decide how the TCP server/client boundary maps to LeRobot async inference and how much of the existing entrypoint behavior remains.
- Keep SO-101 + SmolVLA as the reference config while adding extension points for other arms and policies.
- Decide whether config files should be YAML, Python dataclasses, JSON, or another format that stays easy to inspect and save into run directories.

## Optimization

Server-side operation should eventually include a WebUI. The WebUI should show camera/image streams, joint angles, and runtime state. A useful reference is LeRobot's dataset visualization web experience, but this project should adapt the idea for live server-side experiment monitoring rather than dataset browsing.

Open questions for planning:

- Which image streams should be displayed: robot-side camera frames, model observations, or saved run artifacts?
- Which joint-angle source should be shown: LeRobot robot state, action outputs, or both?
- Should WebUI be read-only monitoring first, or include controls later?
- Should WebUI be served by the policy server process or by a separate lightweight process?
