"""ABL upgrade system: check and apply level-ups based on accumulated experience."""

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


def compute_demand(
    abl_index: int,
    current_level: int,
    aptitude_offset: int,
    config: AblUpgradeConfig,
) -> int:
    abl_def = None
    for d in config.definitions:
        if d.abl_index == abl_index:
            abl_def = d
            break

    if abl_def is None:
        rate = config.default_rate
    else:
        rate = abl_def.rate

    target_level = current_level + 1
    target_index = max(0, target_level - aptitude_offset)

    if target_index >= len(config.explv):
        base_exp = config.explv[-1]
    elif target_index < 0:
        base_exp = config.explv[0]
    else:
        base_exp = config.explv[target_index]

    demand = max(1, int(base_exp * config.default_rate / rate))
    return demand


def check_and_apply_abl_upgrades(
    stats: "ActorNumericState",
    config: AblUpgradeConfig,
    aptitude_offset: int = 0,
) -> list[tuple[int, int, int]]:
    """Check each ABL for level-ups. Returns list of (abl_index, old_level, new_level)."""
    results: list[tuple[int, int, int]] = []

    for definition in config.definitions:
        current_level = stats.compat.abl.get(definition.abl_index)
        if current_level >= len(config.explv) - 1:
            continue

        experience_key = f"abl_{definition.abl_index}"
        experience = stats.source.get(experience_key)

        demand = compute_demand(
            definition.abl_index, current_level, aptitude_offset, config,
        )

        if experience >= demand:
            new_level = current_level + 1
            stats.compat.abl.set(definition.abl_index, new_level)
            results.append((definition.abl_index, current_level, new_level))

    return results