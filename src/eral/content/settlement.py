"""Load SOURCE settlement rules from TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from eral.content.stat_axes import AxisFamily


@dataclass(frozen=True, slots=True)
class SettlementRule:
    """Mapping from CUP index to a target stat block."""

    cup_index: int
    target_family: AxisFamily
    target_index: int
    scale: float = 1.0


def load_settlement_rules(path: Path) -> tuple[SettlementRule, ...]:
    """Load CUP routing rules from TOML."""

    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    return tuple(
        SettlementRule(
            cup_index=int(item.get("cup_index", item["source_index"])),
            target_family=AxisFamily(item["target_family"]),
            target_index=int(item["target_index"]),
            scale=float(item.get("scale", 1)),
        )
        for item in raw_data.get("rules", [])
    )
