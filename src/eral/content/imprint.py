"""Load imprint threshold definitions from TOML."""

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
    """Load imprint thresholds from TOML."""
    if not path.exists():
        return ()

    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    result: list[ImprintThreshold] = []
    for item in raw.get("imprints", []):
        result.append(ImprintThreshold(
            key=item["key"],
            display_name=item["display_name"],
            group=item.get("group", "imprint"),
            palam_key=item.get("palam_key"),
            source_keys=tuple(item.get("source_keys", [])),
            lv1_threshold=int(item.get("lv1_threshold", 0)),
            lv2_threshold=int(item.get("lv2_threshold", 0)),
            lv3_threshold=int(item.get("lv3_threshold", 0)),
        ))
    return tuple(result)