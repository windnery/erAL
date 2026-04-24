"""Load TALENT effect definitions from TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class TalentEffect:
    era_index: int
    label: str
    category: str
    source_key: str
    formula: str
    expression: str
    phase: str = "source"  # source | cup | command | abl


def load_talent_effects(path: Path) -> tuple[TalentEffect, ...]:
    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    return tuple(
        TalentEffect(
            era_index=int(item["era_index"]),
            label=item["label"],
            category=item["category"],
            source_key=item["source_key"],
            formula=item["formula"],
            expression=item["expression"],
            phase=str(item.get("phase", "source")),
        )
        for item in raw_data.get("effect", [])
    )