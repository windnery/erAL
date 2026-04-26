"""Load PALAMLV threshold curves from TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PalamLevel:
    key: int
    threshold: int


@dataclass(frozen=True, slots=True)
class PalamCurve:
    name: str
    description: str
    levels: tuple[PalamLevel, ...]


@dataclass(frozen=True, slots=True)
class PalamToJuelRule:
    """Map one PALAM axis to its corresponding JUEL axis with a divisor."""

    palam_index: int
    juel_index: int
    divisor: int = 100


def load_curves(path: Path) -> PalamCurve:
    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    palam_levels: list[PalamLevel] = []
    for item in raw.get("levels", []):
        palam_levels.append(PalamLevel(key=int(item["key"]), threshold=int(item["threshold"])))

    curve_name = ""
    curve_desc = ""
    for item in raw.get("curve", []):
        if "name" in item:
            curve_name = item["name"]
        if "description" in item:
            curve_desc = item["description"]

    return PalamCurve(
        name=curve_name,
        description=curve_desc,
        levels=tuple(palam_levels),
    )


def load_palam_to_juel_rules(path: Path) -> tuple[PalamToJuelRule, ...]:
    """Load PALAM → JUEL conversion rules from TOML."""

    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    return tuple(
        PalamToJuelRule(
            palam_index=int(item["palam_index"]),
            juel_index=int(item["juel_index"]),
            divisor=int(item.get("divisor", 100)),
        )
        for item in raw.get("rule", [])
    )


def palam_level_for_value(curve: PalamCurve, value: int) -> int:
    """Return the PALAMLV level for a given PALAM accumulated value."""
    result = 0
    for level in curve.levels:
        if value >= level.threshold:
            result = level.key
        else:
            break
    return result
