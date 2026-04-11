"""Load numeric axis definitions copied from eraTW semantics."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class AxisFamily(StrEnum):
    """Supported numeric axis families."""

    BASE = "base"
    PALAM = "palam"
    SOURCE = "source"
    ABL = "abl"
    TALENT = "talent"
    FLAG = "flag"
    CFLAG = "cflag"
    TFLAG = "tflag"


@dataclass(frozen=True, slots=True)
class StatAxis:
    """Single numeric axis imported from an era-style dataset."""

    family: AxisFamily
    key: str
    era_index: int
    label: str
    group: str


@dataclass(slots=True)
class StatAxisCatalog:
    """Resolved numeric axes for all supported families."""

    by_family: dict[AxisFamily, tuple[StatAxis, ...]]
    by_key: dict[tuple[AxisFamily, str], StatAxis]
    by_index: dict[tuple[AxisFamily, int], StatAxis]

    def family_axes(self, family: AxisFamily) -> tuple[StatAxis, ...]:
        return self.by_family.get(family, ())

    def get(self, family: AxisFamily, key: str) -> StatAxis:
        return self.by_key[(family, key)]

    def get_by_index(self, family: AxisFamily, era_index: int) -> StatAxis:
        return self.by_index[(family, era_index)]


def load_stat_axis_catalog(path: Path) -> StatAxisCatalog:
    """Load stat axis metadata from a TOML file."""

    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    by_family: dict[AxisFamily, tuple[StatAxis, ...]] = {}
    by_key: dict[tuple[AxisFamily, str], StatAxis] = {}
    by_index: dict[tuple[AxisFamily, int], StatAxis] = {}

    for family in AxisFamily:
        raw_axes = raw_data.get(family.value, [])
        axes = tuple(
            StatAxis(
                family=family,
                key=item["key"],
                era_index=int(item["era_index"]),
                label=item["label"],
                group=item["group"],
            )
            for item in raw_axes
        )
        by_family[family] = axes

        for axis in axes:
            by_key[(family, axis.key)] = axis
            by_index[(family, axis.era_index)] = axis

    return StatAxisCatalog(by_family=by_family, by_key=by_key, by_index=by_index)
