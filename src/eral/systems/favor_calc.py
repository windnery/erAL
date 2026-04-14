"""Favor and trust growth calculators (FAVOR_CALC / TRUST_CALC)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from eral.domain.stats import ActorNumericState
from eral.domain.world import CharacterState


@dataclass(frozen=True, slots=True)
class TalentModifier:
    era_index: int
    effect: str
    multiplier: float


@dataclass(frozen=True, slots=True)
class GrowthFormula:
    description: str
    base_scale: float
    base_positive_keys: tuple[str, ...]
    base_negative_keys: tuple[str, ...]
    relationship_stage_multiplier: dict[str, float]
    talent_modifiers: tuple[TalentModifier, ...]
    clamp_min: int
    clamp_max: int


def load_growth_formula(path: Path) -> GrowthFormula:
    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    def _load_section(section: dict) -> GrowthFormula:
        return GrowthFormula(
            description=section.get("description", ""),
            base_scale=float(section.get("base_scale", 1.0)),
            base_positive_keys=tuple(section.get("base_positive_keys", [])),
            base_negative_keys=tuple(section.get("base_negative_keys", [])),
            relationship_stage_multiplier=section.get("relationship_stage_multiplier", {}),
            talent_modifiers=tuple(
                TalentModifier(
                    era_index=int(mod["era_index"]),
                    effect=mod["effect"],
                    multiplier=float(mod["multiplier"]),
                )
                for mod in section.get("talent_modifiers", [])
            ),
            clamp_min=int(section.get("clamp_min", 0)),
            clamp_max=int(section.get("clamp_max", 9999)),
        )

    favor_section = raw.get("favor_calc", {})
    return _load_section(favor_section if isinstance(favor_section, dict) else {})


def load_trust_formula(path: Path) -> GrowthFormula:
    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    section = raw.get("trust_calc", {})
    return GrowthFormula(
        description=section.get("description", ""),
        base_scale=float(section.get("base_scale", 1.0)),
        base_positive_keys=tuple(section.get("base_positive_keys", [])),
        base_negative_keys=tuple(section.get("base_negative_keys", [])),
        relationship_stage_multiplier=section.get("relationship_stage_multiplier", {}),
        talent_modifiers=tuple(
            TalentModifier(
                era_index=int(mod["era_index"]),
                effect=mod["effect"],
                multiplier=float(mod["multiplier"]),
            )
            for mod in section.get("talent_modifiers", [])
        ),
        clamp_min=int(section.get("clamp_min", 0)),
        clamp_max=int(section.get("clamp_max", 9999)),
    )


def compute_favor_delta(
    stats: ActorNumericState,
    stage_key: str,
    formula: GrowthFormula,
) -> int:
    positive = sum(stats.source.get(k) for k in formula.base_positive_keys)
    negative = sum(stats.source.get(k) for k in formula.base_negative_keys)
    net = positive - negative
    if net <= 0:
        return 0
    stage_mult = formula.relationship_stage_multiplier.get(stage_key, 1.0)
    talent_mult = 1.0
    for mod in formula.talent_modifiers:
        val = stats.compat.talent.get(mod.era_index)
        if val != 0:
            talent_mult += mod.multiplier * (1 if val > 0 else -1)
    result = int(net * formula.base_scale * stage_mult * talent_mult)
    return max(formula.clamp_min, min(formula.clamp_max, result))


def compute_trust_delta(
    stats: ActorNumericState,
    stage_key: str,
    formula: GrowthFormula,
) -> int:
    positive = sum(stats.source.get(k) for k in formula.base_positive_keys)
    negative = sum(stats.source.get(k) for k in formula.base_negative_keys)
    net = positive - negative
    if net <= 0:
        return 0
    stage_mult = formula.relationship_stage_multiplier.get(stage_key, 1.0)
    talent_mult = 1.0
    for mod in formula.talent_modifiers:
        val = stats.compat.talent.get(mod.era_index)
        if val != 0:
            talent_mult += mod.multiplier * (1 if val > 0 else -1)
    result = int(net * formula.base_scale * stage_mult * talent_mult)
    return max(formula.clamp_min, min(formula.clamp_max, result))