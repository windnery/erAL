"""Load MAXBASE (stamina/spirit ceiling) definitions from TOML."""

from __future__ import annotations

import tomllib
from pathlib import Path


def load_maxbase(path: Path) -> dict[str, int]:
    """Load MAXBASE definitions from TOML, returning {key: max_value}."""
    if not path.exists():
        return {}

    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    result: dict[str, int] = {}
    for item in raw.get("entries", []):
        key = item["key"]
        max_value = int(item["max_value"])
        result[key] = max_value
    return result