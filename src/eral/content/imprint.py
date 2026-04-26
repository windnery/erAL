"""Load imprint threshold definitions from marks.toml."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ImprintThreshold:
    """Defines when a mark imprint is triggered based on CUP/SOURCE accumulation."""

    key: str
    display_name: str
    group: str
    palam_key: str | None
    source_keys: tuple[str, ...]
    lv1_threshold: int
    lv2_threshold: int
    lv3_threshold: int


def load_imprint_thresholds(path: Path) -> tuple[ImprintThreshold, ...]:
    """Load imprint thresholds from marks.toml (shared with MarkDefinition)."""
    if not path.exists():
        return ()

    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    result: list[ImprintThreshold] = []
    for item in raw.get("marks", []):
        # Skip marks without thresholds (e.g. 反发取得履历, 成长)
        if "lv1" not in item:
            continue

        palam_key: str | None = None
        if "palam_index" in item:
            palam_key = str(item["palam_index"])

        source_keys: tuple[str, ...] = ()
        if "source_indices" in item:
            source_keys = tuple(str(i) for i in item["source_indices"])

        result.append(ImprintThreshold(
            key=str(item.get("key", item["index"])),
            display_name=item["display_name"],
            group=item.get("group", "imprint"),
            palam_key=palam_key,
            source_keys=source_keys,
            lv1_threshold=int(item["lv1"]),
            lv2_threshold=int(item.get("lv2", 0)),
            lv3_threshold=int(item.get("lv3", 0)),
        ))
    return tuple(result)