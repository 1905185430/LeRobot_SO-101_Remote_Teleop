---
quick_id: 260511-pto
slug: add-config-driven-lerobot-robot-policy-f
type: quick
status: planned
requirements: []
must_haves:
  truths:
    - "Config-driven LeRobot factory builds SO-101 camera, robot, async client, and server config objects with fake LeRobot modules in tests."
    - "Factory rejects unsupported robot and policy types explicitly."
    - "Existing constant-based policy_server.py and robot_client.py behavior remains unchanged."
    - "Existing tests still pass without real LeRobot installed."
  artifacts:
    - path: "so101_remote/lerobot_factory.py"
      provides: "Config-driven LeRobot config factories"
    - path: "tests/test_lerobot_factory.py"
      provides: "Fake-LeRobot coverage for robot/policy config construction"
---

# Quick Task: Add config-driven LeRobot robot/policy factories

## Scope

Add factories that translate `PlatformConfig` into LeRobot config objects. Keep hardware startup and real policy runtime out of scope for this quick task.

## Tasks

1. Add LeRobot factory module.
   - Files: `so101_remote/lerobot_factory.py`, `so101_remote/__init__.py`
   - Verify: fake LeRobot tests build configs without installing LeRobot.

2. Add tests for supported and unsupported types.
   - Files: `tests/test_lerobot_factory.py`
   - Verify: `python3 -m unittest tests.test_lerobot_factory -v`.

3. Run regression tests.
   - Verify: `python3 -m unittest discover -s tests -v` and `git diff --check`.
