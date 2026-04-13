"""Load MAXBASE (stamina/spirit ceiling) definitions from TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class MaxbaseConfig:
    """Parsed MAXBASE configuration."""

    max_values: dict[str, int]
    recover_rates: dict[str, int]


def load_maxbase(path: Path) -> MaxbaseConfig:
    """Load MAXBASE definitions from TOML, returning max_values and recover_rates."""
    if not path.exists():
        return MaxbaseConfig(max_values={}, recover_rates={})

    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    max_values: dict[str, int] = {}
    recover_rates: dict[str, int] = {}
    for item in raw.get("entries", []):
        key = item["key"]
        max_values[key] = int(item["max_value"])
        recover_rates[key] = int(item.get("recover_rate", 10))
    return MaxbaseConfig(max_values=max_values, recover_rates=recover_rates)