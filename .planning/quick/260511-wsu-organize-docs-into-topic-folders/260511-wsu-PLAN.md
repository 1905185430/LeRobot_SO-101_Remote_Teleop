# Quick Plan: Organize Docs Into Topic Folders

Date: 2026-05-11
Status: Complete

## Goal

Organize top-level docs into topic folders and upload the new structure to GitHub.

## Scope

- Move environment docs to `docs/setup/`.
- Move project overview docs to `docs/project/`.
- Move validation docs to `docs/validation/`.
- Move reproduction and successful-run docs to `docs/reproduction/`.
- Add `docs/README.md` as an index.
- Update README and cross-document links.

## Verification

- `rg` old root doc paths to confirm no stale references remain.
- `git diff --check`
- `python3 -m unittest tests.test_config_loader -v`
