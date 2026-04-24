"""SOURCE_EXTRA executor: applies TALENT multipliers and training mark effects to SOURCE before settlement."""

from __future__ import annotations

from eral.content.talent_effects import TalentEffect
from eral.domain.stats import ActorNumericState
from eral.domain.world import CharacterState


_PLEASURE_KEYS = ("pleasure_c", "pleasure_v", "pleasure_a", "pleasure_b", "pleasure_m")

_MARK_SOURCE_MULTIPLIERS = {
    "pleasure_mark": {
        1: 1.2,
        2: 1.5,
        3: 2.0,
    },
}

_MARK_PAIN_MULTIPLIERS = {
    "pain_mark": {
        1: ({"fear": 1.2}, {}),
        2: ({"fear": 1.5, "obedience": 1.2}, {}),
        3: ({"fear": 2.0, "obedience": 1.5}, {}),
    },
}


def apply_source_extra(
    stats: ActorNumericState,
    effects: tuple[TalentEffect, ...],
) -> dict[str, float]:
    if not effects:
        return {}

    applied: dict[str, float] = {}

    for effect in effects:
        if effect.phase != "source":
            continue
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


def apply_training_mark_effects(actor: CharacterState) -> dict[str, float]:
    """Apply training mark multipliers to SOURCE. Returns applied multipliers."""
    applied: dict[str, float] = {}

    pleasure_level = actor.marks.get("pleasure_mark", 0)
    if pleasure_level > 0:
        mult = _MARK_SOURCE_MULTIPLIERS["pleasure_mark"].get(pleasure_level, 1.0)
        for key in _PLEASURE_KEYS:
            current = actor.stats.source.get(key)
            if current > 0:
                actor.stats.source.set(key, int(current * mult))
                applied[key] = applied.get(key, 1.0) * mult

    pain_level = actor.marks.get("pain_mark", 0)
    if pain_level > 0:
        entry = _MARK_PAIN_MULTIPLIERS["pain_mark"].get(pain_level)
        if entry:
            for source_key, mult in entry[0].items():
                current = actor.stats.source.get(source_key)
                if current > 0:
                    actor.stats.source.set(source_key, int(current * mult))
                    applied[source_key] = applied.get(source_key, 1.0) * mult

    return applied


def _eval_expression(expression: str, v: int) -> float:
    env = {"v": v, "max": max, "min": min, "int": int}
    try:
        return float(eval(expression, {"__builtins__": {}}, env))  # noqa: S307
    except (ZeroDivisionError, ValueError):
        return 1.0