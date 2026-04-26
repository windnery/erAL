"""Apply SOURCE → CUP modifiers using structured CBVA rules (no eval)."""

from __future__ import annotations

from eral.content.palamlv import PalamCurve, palam_level_for_value
from eral.content.source_modifiers import CbvaFactor, SourceCbvaRule
from eral.domain.world import CharacterState


# Standard PALAM thresholds used when no curve is provided.
# Aligned to typical eraTW 欲情 thresholds.
_STANDARD_LEVEL_THRESHOLDS = (0, 1000, 5000, 10000, 50000)


def apply_source_modifiers(
    actor: CharacterState,
    rules: dict[int, SourceCbvaRule],
    palam_curves: dict[int, PalamCurve] | None = None,
) -> None:
    """Transform actor.stats.source into actor.stats.cup using SOURCE_CBVA rules.

    For each SOURCE entry:
      - If a CBVA rule exists, apply its factors multiplicatively.
      - Otherwise, copy the value as-is (identity mapping).
    """

    for key_str, source_value in actor.stats.source.values.items():
        if source_value == 0:
            continue

        source_index = int(key_str)
        rule = rules.get(source_index)
        cup_index = source_index
        cup_value = source_value

        if rule is not None:
            cup_index = rule.cup_index
            for factor in rule.factors:
                mult = _compute_factor(actor, factor, palam_curves)
                cup_value = int(cup_value * mult)

        actor.stats.cup.set(cup_index, cup_value)


def _compute_factor(
    actor: CharacterState,
    factor: CbvaFactor,
    palam_curves: dict[int, PalamCurve] | None,
) -> float:
    """Evaluate a single CBVA factor against actor state."""

    if factor.kind == "sensitivity":
        v = actor.stats.compat.talent.get(factor.index)
        return (2.0 + v) / 2.0

    if factor.kind == "talent_level":
        v = actor.stats.compat.talent.get(factor.index)
        for lvl, mult in factor.levels:
            if v == lvl:
                return mult
        return 1.0

    if factor.kind == "abl_scale":
        v = actor.stats.compat.abl.get(factor.index)
        return 1.0 + v * factor.scale

    if factor.kind == "palam_level":
        raw_value = actor.stats.palam.get(str(factor.index))
        level = _palam_level(raw_value, factor.index, palam_curves)
        for lvl, mult in factor.levels:
            if level == lvl:
                return mult
        return 1.0

    if factor.kind == "talent_linear":
        v = actor.stats.compat.talent.get(factor.index)
        if factor.base == 0:
            return 1.0
        return (factor.base + factor.coeff * v) / factor.base

    return 1.0


def _palam_level(
    value: int,
    palam_index: int,
    palam_curves: dict[int, PalamCurve] | None,
) -> int:
    """Derive PALAM level from raw value."""
    if palam_curves is not None:
        curve = palam_curves.get(palam_index)
        if curve is not None:
            return palam_level_for_value(curve, value)

    # Fallback: use standard thresholds.
    level = 0
    for threshold in _STANDARD_LEVEL_THRESHOLDS[1:]:
        if value >= threshold:
            level += 1
        else:
            break
    return min(level, 4)
