"""SOURCE_EXTRA executor: applies TALENT multipliers to SOURCE before settlement."""

from __future__ import annotations

from eral.content.talent_effects import TalentEffect
from eral.domain.stats import ActorNumericState


def apply_source_extra(
    stats: ActorNumericState,
    effects: tuple[TalentEffect, ...],
) -> dict[str, float]:
    if not effects:
        return {}

    applied: dict[str, float] = {}

    for effect in effects:
        if effect.source_key == "" or effect.formula in ("recovery_modifier", "aptitude_offset"):
            continue

        talent_value = stats.compat.talent.get(effect.era_index)
        if talent_value == 0:
            continue

        current = stats.source.get(effect.source_key)
        if current == 0:
            continue

        if effect.formula == "multiply":
            multiplier = _eval_expression(effect.expression, talent_value)
            new_val = int(current * multiplier)
            if new_val != current:
                stats.source.set(effect.source_key, new_val)
                applied[effect.source_key] = applied.get(effect.source_key, 1.0) * multiplier

        elif effect.formula == "add":
            bonus = int(_eval_expression(effect.expression, talent_value))
            if bonus != 0:
                stats.source.add(effect.source_key, bonus)
                applied[effect.source_key] = applied.get(effect.source_key, 0.0) + bonus

    return applied


def compute_recovery_modifier(
    stats: ActorNumericState,
    effects: tuple[TalentEffect, ...],
) -> float:
    for effect in effects:
        if effect.category != "recovery":
            continue
        talent_value = stats.compat.talent.get(effect.era_index)
        if talent_value == 0:
            continue
        return _eval_expression(effect.expression, talent_value)
    return 1.0


def compute_aptitude_offset(
    stats: ActorNumericState,
    effects: tuple[TalentEffect, ...],
) -> int:
    for effect in effects:
        if effect.formula != "aptitude_offset":
            continue
        talent_value = stats.compat.talent.get(effect.era_index)
        if talent_value == 0:
            continue
        return talent_value
    return 0


def _eval_expression(expression: str, v: int) -> float:
    env = {"v": v, "max": max, "min": min, "int": int}
    try:
        return float(eval(expression, {"__builtins__": {}}, env))  # noqa: S307
    except (ZeroDivisionError, ValueError):
        return 1.0