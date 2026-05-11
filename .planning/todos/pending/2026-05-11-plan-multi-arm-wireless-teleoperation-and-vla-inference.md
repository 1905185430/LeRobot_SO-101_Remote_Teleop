---
created: 2026-05-11T09:35:41.179Z
title: Plan multi-arm wireless teleoperation and VLA inference
area: general
files:
  - .planning/ROADMAP.md
  - .planning/PROJECT.md
  - legacy/
  - so101_remote/
---

## Problem

Future experiments need to support multiple robot arms, wireless teleoperation,
and VLA inference workflows instead of staying focused only on the first SO-101
+ SmolVLA path. This is needed for convenience when expanding the project to
new hardware and new experiment modes.

Current roadmap/project context already mentions future robot arms, PI-series
policies, and later teleoperation integration, but the combined product need
has not been captured as a concrete planning item.

## Solution

TBD during future roadmap planning. Likely work:

- Define how multiple robot arms are selected and described without turning v1
  into a heavy plugin platform.
- Decide how legacy wireless teleoperation should integrate with the current
  metrics/run-artifact system.
- Clarify how teleoperation and VLA inference modes coexist in the operator
  workflow.
- Preserve SO-101 + SmolVLA as the stable first path while adding extension
  points for later arms and policies.
