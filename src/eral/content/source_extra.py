"""Load SOURCE_EXTRA modifier definitions from TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SourceExtraCondition:
    """Single condition for a SOURCE_EXTRA modifier."""

    kind: str  # talent_value | talent_present | talent_level
    talent_index: int = 0
    base: int = 10
    coeff: int = 0
    multiplier: float = 1.0
    levels: tuple[tuple[int, float], ...] = ()


@dataclass(frozen=True, slots=True)
class SourceExtraModifier:
    """Global modifier applied to one or more SOURCE keys."""

    target_sources: tuple[str, ...]
    description: str = ""
    operation: str = "multiply"
    conditions: tuple[SourceExtraCondition, ...] = ()


def _parse_levels(raw: dict) -> tuple[tuple[int, float], ...]:
    return tuple(
        (int(level), float(mult))
        for level, mult in sorted(raw.items(), key=lambda x: int(x[0]))
    )


def load_source_extra_modifiers(path: Path) -> tuple[SourceExtraModifier, ...]:
    """Load SOURCE_EXTRA modifiers."""

    if not path.exists():
        return ()

    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    modifiers: list[SourceExtraModifier] = []
    for item in raw.get("modifier", []):
        conditions: list[SourceExtraCondition] = []
        for c in item.get("condition", []):
            kind = str(c["kind"])
            if kind == "talent_value":
                conditions.append(
                    SourceExtraCondition(
                        kind=kind,
                        talent_index=int(c["talent_index"]),
                        base=int(c.get("base", 10)),
                        coeff=int(c.get("coeff", 0)),
                    )
                )
            elif kind == "talent_present":
                conditions.append(
                    SourceExtraCondition(
                        kind=kind,
                        talent_index=int(c["talent_index"]),
                        multiplier=float(c.get("multiplier", 1.0)),
                    )
                )
            elif kind == "talent_level":
                conditions.append(
                    SourceExtraCondition(
                        kind=kind,
                        talent_index=int(c["talent_index"]),
                        levels=_parse_levels(c.get("levels", {})),
                    )
                )

        modifiers.append(
            SourceExtraModifier(
                target_sources=tuple(str(s) for s in item.get("target_sources", [])),
                description=str(item.get("description", "")),
                operation=str(item.get("operation", "multiply")),
                conditions=tuple(conditions),
            )
        )

    return tuple(modifiers)
