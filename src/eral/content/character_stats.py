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

    base_values, base_caps, base_recover_rates = _load_base_family(
        path / "base.toml",
        stat_axes=stat_axes,
    )
    return InitialStatOverrides(
        base=base_values,
        base_caps=base_caps,
        base_recover_rates=base_recover_rates,
        palam=_load_named_family(path / "palam.toml", family=AxisFamily.PALAM, stat_axes=stat_axes),
        abl=_load_indexed_family(path / "abl.toml", family=AxisFamily.ABL, stat_axes=stat_axes),
        talent=_load_indexed_family(path / "talent.toml", family=AxisFamily.TALENT, stat_axes=stat_axes),
        cflag=_load_indexed_family(path / "cflag.toml", family=AxisFamily.CFLAG, stat_axes=stat_axes),
        marks=_load_marks(path / "marks.toml", mark_keys=mark_keys),
    )


def _load_base_family(
    path: Path,
    *,
    stat_axes: StatAxisCatalog,
) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    """Load character BASE initial values plus optional caps/recovery.

    Legacy flat tables are still accepted and interpreted as initial values
    only. Explicit [cap] / [recover] tables opt a character into actor-specific
    limits and recovery behavior.
    """

    raw_values = _load_toml_table(path)
    if not raw_values:
        return {}, {}, {}

    uses_explicit_tables = any(
        isinstance(raw_values.get(section), dict)
        for section in ("current", "initial", "cap", "recover")
    )
    if not uses_explicit_tables:
        initial_values = _validate_named_family(
            raw_values,
            family=AxisFamily.BASE,
            stat_axes=stat_axes,
        )
        return initial_values, {}, {}

    initial_table = raw_values.get("current")
    if initial_table is None:
        initial_table = raw_values.get("initial", {})
    cap_table = raw_values.get("cap", {})
    recover_table = raw_values.get("recover", {})
    if not isinstance(initial_table, dict):
        raise TypeError(f"{path} [current]/[initial] must be a table")
    if not isinstance(cap_table, dict):
        raise TypeError(f"{path} [cap] must be a table")
    if not isinstance(recover_table, dict):
        raise TypeError(f"{path} [recover] must be a table")

    initial_values = _validate_named_family(
        initial_table,
        family=AxisFamily.BASE,
        stat_axes=stat_axes,
    )
    cap_values = _validate_named_family(
        cap_table,
        family=AxisFamily.BASE,
        stat_axes=stat_axes,
    )
    recover_values = _validate_named_family(
        recover_table,
        family=AxisFamily.BASE,
        stat_axes=stat_axes,
    )
    for key, value in initial_values.items():
        cap_values.setdefault(key, value)
    return initial_values, cap_values, recover_values


def _load_named_family(
    path: Path,
    *,
    family: AxisFamily,
    stat_axes: StatAxisCatalog,
) -> dict[str, int]:
    raw_values = _load_toml_table(path)
    return _validate_named_family(raw_values, family=family, stat_axes=stat_axes)


def _validate_named_family(
    raw_values: dict[str, object],
    *,
    family: AxisFamily,
    stat_axes: StatAxisCatalog,
) -> dict[str, int]:
    values: dict[str, int] = {}
    for key, value in raw_values.items():
        stat_axes.get(family, str(key))
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
            raise KeyError(f"Unknown mark key '{key}' in {path}")
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
