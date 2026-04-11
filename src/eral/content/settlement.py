"""Load SOURCE settlement rules from TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from eral.content.stat_axes import AxisFamily


@dataclass(frozen=True, slots=True)
class SettlementRule:
    """Mapping from SOURCE key to a target stat block."""

    source: str
    target_family: AxisFamily
    target_key: str | None = None
    target_index: int | None = None
    scale: int = 1


def load_settlement_rules(path: Path) -> tuple[SettlementRule, ...]:
    """Load settlement rules from TOML."""

    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    return tuple(
        SettlementRule(
            source=item["source"],
            target_family=AxisFamily(item["target_family"]),
            target_key=item.get("target_key"),
            target_index=item.get("target_index"),
            scale=int(item.get("scale", 1)),
        )
        for item in raw_data.get("rules", [])
    )

