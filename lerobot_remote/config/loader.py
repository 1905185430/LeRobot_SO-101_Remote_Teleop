"""Config file loading helpers for platform modes."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from .schema import ConfigError, PlatformConfig, platform_config_from_mapping

_INT_RE = re.compile(r"^[+-]?[0-9]+$")
_FLOAT_RE = re.compile(r"^[+-]?([0-9]+\.[0-9]+|[0-9]+[eE][+-]?[0-9]+)$")


def load_config(path: str | Path) -> PlatformConfig:
    """Load a platform config from JSON or simple YAML."""
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    text = config_path.read_text(encoding="utf-8")
    if config_path.suffix.lower() == ".json":
        raw = json.loads(text)
    elif config_path.suffix.lower() in {".yaml", ".yml"}:
        raw = parse_simple_yaml(text)
    else:
        raise ConfigError("Config files must use .yaml, .yml, or .json extension.")

    if not isinstance(raw, dict):
        raise ConfigError("Config root must be a mapping.")
    return platform_config_from_mapping(raw, source_path=config_path)


def parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse the simple YAML subset used by bundled configs.

    This intentionally supports nested mappings and scalar values only. It avoids
    adding a PyYAML dependency while keeping the config files human-readable.
    """
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = _strip_comment(raw_line).rstrip()
        if not line.strip():
            continue
        if line.lstrip().startswith("- "):
            raise ConfigError(f"YAML lists are not supported at line {line_number}.")

        indent = len(line) - len(line.lstrip(" "))
        if indent % 2 != 0:
            raise ConfigError(f"Indentation must use multiples of 2 spaces at line {line_number}.")

        stripped = line.strip()
        if ":" not in stripped:
            raise ConfigError(f"Expected 'key: value' at line {line_number}.")
        key, value = stripped.split(":", 1)
        key = key.strip()
        if not key:
            raise ConfigError(f"Missing key at line {line_number}.")

        while indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        value = value.strip()
        if value == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(value)

    return root


def _strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    for index, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:index]
    return line


def _parse_scalar(value: str) -> object:
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]

    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    if _INT_RE.match(value):
        return int(value)
    if _FLOAT_RE.match(value):
        return float(value)
    return value
