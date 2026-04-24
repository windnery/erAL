"""Load SOURCE → CUP modifier definitions from TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ModifierFactor:
    """Single multiplicative factor in a SOURCE → CUP modifier."""

    kind: str  # talent | abl | palam_level
    index: int
    expr: str = "1.0"


@dataclass(frozen=True, slots=True)
class SourceModifier:
    """Defines how one SOURCE index is transformed into a CUP index."""

    source_index: int
    cup_index: int
    factors: tuple[ModifierFactor, ...] = ()


def load_source_modifiers(path: Path) -> dict[int, SourceModifier]:
    """Load source modifiers keyed by source_index."""

    if not path.exists():
        return {}

    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    result: dict[int, SourceModifier] = {}
    for item in raw.get("modifier", []):
        factors = tuple(
            ModifierFactor(
                kind=str(f["kind"]),
                index=int(f["index"]),
                expr=str(f.get("expr", "1.0")),
            )
            for f in item.get("factors", [])
        )
        modifier = SourceModifier(
            source_index=int(item["source_index"]),
            cup_index=int(item.get("cup_index", item["source_index"])),
            factors=factors,
        )
        result[modifier.source_index] = modifier

    return result
