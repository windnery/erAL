"""Load SOURCE_CBVA rules from TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CbvaFactor:
    """Single multiplicative factor in a SOURCE_CBVA rule."""

    kind: str  # sensitivity | abl_scale | palam_level | talent_linear
    index: int = 0
    scale: float = 0.0
    base: int = 0
    coeff: int = 0
    levels: tuple[tuple[int, float], ...] = ()


@dataclass(frozen=True, slots=True)
class SourceCbvaRule:
    """Defines how one SOURCE index is transformed into a CUP index."""

    source_index: int
    cup_index: int
    factors: tuple[CbvaFactor, ...] = ()


def _parse_levels(raw: dict) -> tuple[tuple[int, float], ...]:
    return tuple(
        (int(level), float(mult))
        for level, mult in sorted(raw.items(), key=lambda x: int(x[0]))
    )


def load_source_cbva_rules(path: Path) -> dict[int, SourceCbvaRule]:
    """Load SOURCE_CBVA rules keyed by source_index."""

    if not path.exists():
        return {}

    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    result: dict[int, SourceCbvaRule] = {}
    for item in raw.get("rule", []):
        factors: list[CbvaFactor] = []
        for f in item.get("factor", []):
            kind = str(f["kind"])
            if kind == "sensitivity":
                factors.append(
                    CbvaFactor(
                        kind=kind,
                        index=int(f["talent_index"]),
                    )
                )
            elif kind == "abl_scale":
                factors.append(
                    CbvaFactor(
                        kind=kind,
                        index=int(f["abl_index"]),
                        scale=float(f.get("scale", 0.1)),
                    )
                )
            elif kind == "palam_level":
                factors.append(
                    CbvaFactor(
                        kind=kind,
                        index=int(f["palam_index"]),
                        levels=_parse_levels(f.get("levels", {})),
                    )
                )
            elif kind == "talent_linear":
                factors.append(
                    CbvaFactor(
                        kind=kind,
                        index=int(f["talent_index"]),
                        base=int(f.get("base", 10)),
                        coeff=int(f.get("coeff", 0)),
                    )
                )
            elif kind == "talent_level":
                factors.append(
                    CbvaFactor(
                        kind=kind,
                        index=int(f["talent_index"]),
                        levels=_parse_levels(f.get("levels", {})),
                    )
                )

        rule = SourceCbvaRule(
            source_index=int(item["source_index"]),
            cup_index=int(item.get("cup_index", item["source_index"])),
            factors=tuple(factors),
        )
        result[rule.source_index] = rule

    return result
