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
    """Load stat axis metadata.

    Two supported layouts:
      - Directory: ``path`` is ``data/base/axes/`` containing
        ``base.toml``, ``palam.toml``, ``source.toml``, ``abl.toml``,
        ``talent.toml`` (each with ``[[entries]]`` blocks).
      - Legacy: ``path`` is a single ``stat_axes.toml`` with
        ``[[base]]``/``[[palam]]``/``[[source]]`` blocks.
    """

    by_family: dict[AxisFamily, tuple[StatAxis, ...]] = {}
    by_key: dict[tuple[AxisFamily, str], StatAxis] = {}
    by_index: dict[tuple[AxisFamily, int], StatAxis] = {}

    def _emit(family: AxisFamily, items: list[dict]) -> None:
        axes = tuple(
            StatAxis(
                family=family,
                key=item.get("key", str(item["index"])),
                era_index=int(item.get("era_index", item["index"])),
                label=item["label"],
            )
            for item in items
        )
        by_family[family] = axes
        for axis in axes:
            by_key[(family, axis.key)] = axis
            by_index[(family, axis.era_index)] = axis

    if path.is_dir():
        for family in AxisFamily:
            file_path = path / f"{family.value}.toml"
            if not file_path.exists():
                by_family[family] = ()
                continue
            with file_path.open("rb") as handle:
                raw = tomllib.load(handle)
            _emit(family, raw.get(family.value, []))
    else:
        with path.open("rb") as handle:
            raw_data = tomllib.load(handle)
        for family in AxisFamily:
            _emit(family, raw_data.get(family.value, []))

    return StatAxisCatalog(by_family=by_family, by_key=by_key, by_index=by_index)
