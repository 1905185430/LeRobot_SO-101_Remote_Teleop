---
quick_id: 260511-qzk
slug: add-tcp-teleop-action-delta-safety-limit
type: quick
status: planned
requirements: []
must_haves:
  truths:
    - "TCP teleop follower reads startup position when available."
    - "TCP teleop follower limits per-frame action deltas before send_action."
    - "Tests cover large first target clamping."
  artifacts:
    - path: "so101_remote/teleop_tcp.py"
      provides: "Action delta safety limit"
---

# Quick Task: Add TCP teleop action delta safety limit

## Scope

Reduce large unexpected follower motion by making the follower side initialize from its current joint state and clamp received action deltas before sending them to hardware.
