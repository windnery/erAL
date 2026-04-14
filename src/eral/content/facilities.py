"""Facility definition loader for the port development system."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import tomllib


@dataclass(frozen=True, slots=True)
class FacilityEffect:
    """A single effect granted by a facility at a given level."""

    type: str
    params: dict[str, int | float | str]
    min_level: int = 1


@dataclass(frozen=True, slots=True)
class FacilityDefinition:
    """Static facility definition loaded from TOML."""

    key: str
    display_name: str
    max_level: int
    upgrade_costs: tuple[int, ...]
    effects: tuple[FacilityEffect, ...]


def load_facility_definitions(path: Path) -> tuple[FacilityDefinition, ...]:
    """Load facility definitions from a TOML file."""
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    results: list[FacilityDefinition] = []
    for entry in raw.get("facilities", []):
        effects: list[FacilityEffect] = []
        for eff in entry.get("effects", []):
            effects.append(
                FacilityEffect(
                    type=eff["type"],
                    params=dict(eff.get("params", {})),
                    min_level=eff.get("min_level", 1),
                )
            )
        results.append(
            FacilityDefinition(
                key=entry["key"],
                display_name=entry["display_name"],
                max_level=entry["max_level"],
                upgrade_costs=tuple(entry.get("upgrade_costs", [])),
                effects=tuple(effects),
            )
        )
    return tuple(results)
