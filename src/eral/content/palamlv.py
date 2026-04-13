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
class ExplvCurve:
    levels: tuple[PalamLevel, ...]


@dataclass(frozen=True, slots=True)
class CurveSet:
    palam_curve: PalamCurve
    exp_curve: ExplvCurve


def load_curves(path: Path) -> CurveSet:
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

    exp_levels: list[PalamLevel] = []
    for item in raw.get("exp_levels", []):
        exp_levels.append(PalamLevel(key=int(item["key"]), threshold=int(item["threshold"])))

    return CurveSet(
        palam_curve=PalamCurve(
            name=curve_name,
            description=curve_desc,
            levels=tuple(palam_levels),
        ),
        exp_curve=ExplvCurve(levels=tuple(exp_levels)),
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


def exp_level_for_value(exp_curve: ExplvCurve, value: int) -> int:
    """Return the EXPLV level for a given accumulated EXP value."""
    result = 0
    for level in exp_curve.levels:
        if value >= level.threshold:
            result = level.key
        else:
            break
    return result