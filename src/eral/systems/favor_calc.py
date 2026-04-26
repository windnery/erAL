"""Favor and trust growth calculators (FAVOR_CALC / TRUST_CALC)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from eral.domain.stats import ActorNumericState
from eral.domain.world import CharacterState


@dataclass(frozen=True, slots=True)
class SourceContribution:
    """Upper-bound formula for one SOURCE key."""

    key: str
    numerator: int
    denominator_k: int
    denominator_offset: int
    scale: float = 1.0
    abl_modifier: tuple[int, int, int] | None = None  # (abl_index, offset, divisor)
    talent_modifier: tuple[int, int, int] | None = None  # (era_index, offset, divisor)


@dataclass(frozen=True, slots=True)
class BaseOffset:
    """Flat offset from ABL or TALENT."""

    kind: str  # "abl" | "abl_sum" | "talent_fixed"
    value: int = 0
    abl_indices: tuple[int, ...] = ()
    divisor: int = 1
    era_index: int = 0
    condition: str = ""


@dataclass(frozen=True, slots=True)
class GrowthFormula:
    """Complete formula definition matching eraTW semantics."""

    description: str
    global_divisor: int
    base_offsets: tuple[BaseOffset, ...]
    sources: tuple[SourceContribution, ...]
    stage_multiplier: dict[str, float]
    mark_floor: dict[int, int]  # mark_level -> minimum_delta


def _parse_base_offsets(raw_list: list[dict]) -> tuple[BaseOffset, ...]:
    offsets: list[BaseOffset] = []
    for item in raw_list:
        kind = str(item["kind"])
        if kind == "abl_sum":
            offsets.append(
                BaseOffset(
                    kind=kind,
                    abl_indices=tuple(int(v) for v in item.get("abl_indices", [])),
                    divisor=int(item.get("divisor", 1)),
                )
            )
        elif kind == "abl":
            offsets.append(
                BaseOffset(
                    kind=kind,
                    era_index=int(item.get("era_index", 0)),
                    divisor=int(item.get("divisor", 1)),
                )
            )
        elif kind == "talent_fixed":
            offsets.append(
                BaseOffset(
                    kind=kind,
                    era_index=int(item["era_index"]),
                    value=int(item.get("value", 0)),
                    condition=str(item.get("condition", "")),
                )
            )
    return tuple(offsets)


def _parse_sources(raw_list: list[dict]) -> tuple[SourceContribution, ...]:
    sources: list[SourceContribution] = []
    for item in raw_list:
        abl_mod = None
        if "abl_modifier" in item:
            am = item["abl_modifier"]
            abl_mod = (int(am["abl_index"]), int(am["offset"]), int(am["divisor"]))
        talent_mod = None
        if "talent_modifier" in item:
            tm = item["talent_modifier"]
            talent_mod = (int(tm["era_index"]), int(tm["offset"]), int(tm["divisor"]))
        sources.append(
            SourceContribution(
                key=str(item["key"]),
                numerator=int(item.get("numerator", 100)),
                denominator_k=int(item.get("denominator_k", 100000)),
                denominator_offset=int(item.get("denominator_offset", 1000)),
                scale=float(item.get("scale", 1.0)),
                abl_modifier=abl_mod,
                talent_modifier=talent_mod,
            )
        )
    return tuple(sources)


def _parse_mark_floor(raw: dict | None) -> dict[int, int]:
    if raw is None:
        return {}
    levels = raw.get("levels", {})
    return {int(k): int(v) for k, v in levels.items()}


def _load_formula(section: dict) -> GrowthFormula:
    return GrowthFormula(
        description=str(section.get("description", "")),
        global_divisor=int(section.get("global_divisor", 10)),
        base_offsets=_parse_base_offsets(section.get("base_offset", [])),
        sources=_parse_sources(section.get("source", [])),
        stage_multiplier=dict(section.get("stage_multiplier", {})),
        mark_floor=_parse_mark_floor(section.get("boundary", {}).get("mark_floor")),
    )


def load_growth_formula(path: Path) -> GrowthFormula:
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    section = raw.get("favor_calc", {})
    return _load_formula(section)


def load_trust_formula(path: Path) -> GrowthFormula:
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    section = raw.get("trust_calc", {})
    return _load_formula(section)


def _compute_source_contribution(
    stats: ActorNumericState,
    source: SourceContribution,
) -> float:
    """Evaluate one SOURCE contribution using the upper-bound formula."""
    source_value = stats.source.get(source.key)
    if source_value <= 0:
        return 0.0

    denominator = source.denominator_k / (source_value + source.denominator_offset)
    contribution = (source.numerator - denominator) * source.scale

    # ABL modifier
    if source.abl_modifier is not None:
        abl_index, offset, divisor = source.abl_modifier
        abl_val = stats.compat.abl.get(abl_index)
        contribution *= (abl_val + offset) / divisor

    # Talent modifier
    if source.talent_modifier is not None:
        era_index, offset, divisor = source.talent_modifier
        talent_val = stats.compat.talent.get(era_index)
        contribution *= (talent_val + offset) / divisor

    return contribution


def _compute_base_offsets(stats: ActorNumericState, offsets: tuple[BaseOffset, ...]) -> int:
    """Sum all flat base offsets."""
    total = 0
    for offset in offsets:
        if offset.kind == "abl_sum":
            total += sum(stats.compat.abl.get(idx) for idx in offset.abl_indices) // offset.divisor
        elif offset.kind == "abl":
            total += stats.compat.abl.get(offset.era_index) // offset.divisor
        elif offset.kind == "talent_fixed":
            val = stats.compat.talent.get(offset.era_index)
            cond = offset.condition
            if cond == "value > 0" and val > 0:
                total += offset.value
            elif cond == "value < 0" and val < 0:
                total += offset.value
            elif cond == "value != 0" and val != 0:
                total += offset.value
    return total


def _compute_growth_delta(
    stats: ActorNumericState,
    stage_key: str,
    formula: GrowthFormula,
) -> int:
    """Generic growth delta calculator matching eraTW FAVOR/TRUST_CALC."""
    # SOURCE contributions
    source_total = sum(
        _compute_source_contribution(stats, source) for source in formula.sources
    )

    # Base offsets
    offset_total = _compute_base_offsets(stats, formula.base_offsets)

    # Pre-divisor sum
    raw = source_total + offset_total
    if raw <= 0:
        return 0

    delta = int(raw / formula.global_divisor)

    # Stage multiplier
    stage_mult = formula.stage_multiplier.get(stage_key, 1.0)
    delta = int(delta * stage_mult)

    # Mark floor
    if formula.mark_floor:
        # Find applicable mark level (placeholder: use resentment mark if present)
        # In full implementation this would read from actor.marks
        pass

    return max(0, delta)


def compute_favor_delta(
    stats: ActorNumericState,
    stage_key: str,
    formula: GrowthFormula,
) -> int:
    return _compute_growth_delta(stats, stage_key, formula)


def compute_trust_delta(
    stats: ActorNumericState,
    stage_key: str,
    formula: GrowthFormula,
) -> int:
    return _compute_growth_delta(stats, stage_key, formula)
