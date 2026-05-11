---
quick_id: 260511-pof
slug: add-minimal-tcp-protocol-client-server-m
type: quick
status: planned
requirements: []
must_haves:
  truths:
    - "TCP protocol uses a 4-byte length prefix before each JSON payload."
    - "Client and server helpers can perform one mock observation/action round trip without LeRobot or hardware."
    - "Protocol validates message types and max packet size."
    - "Existing tests still pass."
  artifacts:
    - path: "so101_remote/network/protocol.py"
      provides: "Length-prefixed TCP message encoding and decoding"
    - path: "so101_remote/network/tcp_client.py"
      provides: "Small TCP client helper for observation/action exchange"
    - path: "so101_remote/network/tcp_server.py"
      provides: "Small one-client TCP server helper for mock policy exchange"
---

# Quick Task: Add minimal TCP protocol client/server mock roundtrip

## Scope

Add the first real network layer: length-prefixed JSON messages over TCP plus testable client/server helpers. Do not connect real cameras, robot hardware, model inference, or WebUI yet.

## Tasks

1. Add network package and protocol helpers.
   - Files: `so101_remote/network/__init__.py`, `so101_remote/network/protocol.py`
   - Verify: unit tests cover encode/decode, length prefix, type validation, and max size.

2. Add TCP client/server helpers.
   - Files: `so101_remote/network/tcp_client.py`, `so101_remote/network/tcp_server.py`
   - Verify: one mock observation produces one mock action through a localhost TCP round trip.

3. Add tests and docs.
   - Files: `tests/test_tcp_network.py`, `README.md`
   - Verify: `python3 -m unittest tests.test_tcp_network -v`, `python3 -m unittest discover -s tests -v`, and `git diff --check`.
