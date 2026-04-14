"""Load ABL upgrade threshold definitions."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AblDefinition:
    abl_index: int
    label: str
    base_demand: int
    rate: float


@dataclass(frozen=True, slots=True)
class AblUpgradeConfig:
    default_rate: float
    explv: tuple[int, ...]
    definitions: tuple[AblDefinition, ...]


def load_abl_upgrade_config(path: Path) -> AblUpgradeConfig:
    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    defaults = raw.get("defaults", {})
    default_rate = float(defaults.get("default_rate", 1.0))

    explv_raw = raw.get("explv", {})
    max_level = max(int(k) for k in explv_raw.keys()) if explv_raw else 0
    explv = tuple(explv_raw.get(str(i), 10000) for i in range(max_level + 2))

    definitions = tuple(
        AblDefinition(
            abl_index=int(item["abl_index"]),
            label=item["label"],
            base_demand=int(item.get("base_demand", 1)),
            rate=float(item.get("rate", default_rate)),
        )
        for item in raw.get("abl", [])
    )

    return AblUpgradeConfig(
        default_rate=default_rate,
        explv=explv,
        definitions=definitions,
    )
