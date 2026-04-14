"""Load commission definitions from TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CommissionDefinition:
    key: str
    display_name: str
    duration_slots: int
    min_stage: str | None = None
    port_income: int = 0


def load_commission_definitions(path: Path) -> tuple[CommissionDefinition, ...]:
    if not path.exists():
        return ()
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    return tuple(
        CommissionDefinition(
            key=item["key"],
            display_name=item["display_name"],
            duration_slots=int(item["duration_slots"]),
            min_stage=item.get("min_stage"),
            port_income=int(item.get("port_income", 0)),
        )
        for item in raw.get("commissions", [])
    )
