"""Load split character stat override files."""

from __future__ import annotations

import tomllib
from pathlib import Path

from eral.content.characters import InitialStatOverrides
from eral.content.stat_axes import AxisFamily, StatAxisCatalog


def load_split_initial_stats(
    path: Path,
    *,
    stat_axes: StatAxisCatalog,
    mark_keys: set[str],
) -> InitialStatOverrides | None:
    """Load split stat files from a character pack directory."""

    has_split_files = any((path / file_name).exists() for file_name in _SPLIT_STAT_FILES)
    if not has_split_files:
        return None

    return InitialStatOverrides(
        base=_load_named_family(path / "base.toml", family=AxisFamily.BASE, stat_axes=stat_axes),
        palam=_load_named_family(path / "palam.toml", family=AxisFamily.PALAM, stat_axes=stat_axes),
        abl=_load_indexed_family(path / "abl.toml", family=AxisFamily.ABL, stat_axes=stat_axes),
        talent=_load_indexed_family(path / "talent.toml", family=AxisFamily.TALENT, stat_axes=stat_axes),
        cflag=_load_indexed_family(path / "cflag.toml", family=AxisFamily.CFLAG, stat_axes=stat_axes),
        marks=_load_marks(path / "marks.toml", mark_keys=mark_keys),
    )


def _load_named_family(
    path: Path,
    *,
    family: AxisFamily,
    stat_axes: StatAxisCatalog,
) -> dict[str, int]:
    raw_values = _load_toml_table(path)
    values: dict[str, int] = {}
    for key, value in raw_values.items():
        try:
            stat_axes.get(family, str(key))
        except KeyError as exc:
            raise ValueError(f"Unknown {family.value} stat key: {key}") from exc
        values[str(key)] = int(value)
    return values


def _load_indexed_family(
    path: Path,
    *,
    family: AxisFamily,
    stat_axes: StatAxisCatalog,
) -> dict[int, int]:
    raw_values = _load_toml_table(path)
    values: dict[int, int] = {}
    for key, value in raw_values.items():
        era_index = int(key)
        try:
            stat_axes.get_by_index(family, era_index)
        except KeyError as exc:
            raise ValueError(f"Unknown {family.value} stat key: {key}") from exc
        values[era_index] = int(value)
    return values


def _load_marks(path: Path, *, mark_keys: set[str]) -> dict[str, int]:
    raw_values = _load_toml_table(path)
    values: dict[str, int] = {}
    for key, value in raw_values.items():
        if str(key) not in mark_keys:
            raise ValueError(f"Unknown mark key: {key}")
        values[str(key)] = int(value)
    return values


def _load_toml_table(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)
    return dict(raw_data)


_SPLIT_STAT_FILES = (
    "base.toml",
    "palam.toml",
    "abl.toml",
    "talent.toml",
    "cflag.toml",
    "marks.toml",
)
