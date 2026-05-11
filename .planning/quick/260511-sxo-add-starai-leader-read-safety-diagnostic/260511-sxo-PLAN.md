---
quick_id: 260511-sxo
slug: add-starai-leader-read-safety-diagnostic
type: quick
status: planned
requirements: []
must_haves:
  truths:
    - "Leader get_action failures are wrapped before any command is sent."
    - "Operator receives a clear hardware-read diagnostic."
    - "Existing safety tests pass."
  artifacts:
    - path: "so101_remote/teleop_tcp.py"
      provides: "Leader action read safety wrapper"
---

# Quick Task: Add StarAI leader read safety diagnostics

## Scope

Improve TCP teleop leader-side safety diagnostics when StarAI/FashionStar returns no motor position and the underlying package raises a low-level TypeError.
