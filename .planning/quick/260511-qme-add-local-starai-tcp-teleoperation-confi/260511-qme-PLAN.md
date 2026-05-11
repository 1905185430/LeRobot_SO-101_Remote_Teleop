---
quick_id: 260511-qme
slug: add-local-starai-tcp-teleoperation-confi
type: quick
status: planned
requirements: []
must_haves:
  truths:
    - "Add a dedicated local StarAI TCP teleoperation YAML config."
    - "Config uses 127.0.0.1 so server and client can run on the same machine."
    - "Config validates through both server and client dry-run entrypoints."
  artifacts:
    - path: "configs/local_teleop_starai_tcp.yaml"
      provides: "Local StarAI TCP teleoperation config"
---

# Quick Task: Add local StarAI TCP teleoperation config

## Scope

Add a standalone YAML config for running StarAI leader and follower on one host through the same TCP teleoperation runtime.
