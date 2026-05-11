# Quick Plan: Document Config Categories And Validation Reproduction Commands

Date: 2026-05-11
Status: Complete

## Goal

Make the configuration files easier to understand by type and provide a Chinese reproduction guide for the StarAI local TCP teleoperation validation that just passed.

## Scope

- Add a config classification document under `configs/`.
- Add a reproduction document under `docs/` with startup and test commands.
- Include the current StarAI calibration paths, server/client commands, dry-run commands, and automated test commands.
- Keep existing config file paths unchanged so current operator commands continue to work.

## Verification

- `python3 -m unittest tests.test_config_loader tests.test_starai tests.test_tcp_teleop -v`
- Path checks for the local StarAI config and both project-local calibration JSON files.
