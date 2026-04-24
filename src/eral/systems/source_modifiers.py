"""Apply SOURCE → CUP modifiers using TALENT, ABL, and PALAM state."""

from __future__ import annotations

from eral.content.source_modifiers import SourceModifier
from eral.domain.world import CharacterState


def apply_source_modifiers(
    actor: CharacterState,
    modifiers: dict[int, SourceModifier],
) -> None:
    """Transform actor.stats.source into actor.stats.cup.

    For each SOURCE entry:
      - If a modifier exists, apply its factors multiplicatively.
      - Otherwise, copy the value as-is (identity mapping).
    """

    for key_str, source_value in actor.stats.source.values.items():
        if source_value == 0:
            continue

        source_index = int(key_str)
        modifier = modifiers.get(source_index)
        cup_index = source_index
        cup_value = source_value

        if modifier is not None:
            cup_index = modifier.cup_index
            for factor in modifier.factors:
                mult = _compute_factor(actor, factor)
                cup_value = int(cup_value * mult)

        actor.stats.cup.set(cup_index, cup_value)


def _compute_factor(actor: CharacterState, factor) -> float:  # noqa: ANN001
    """Evaluate a single modifier factor against actor state."""

    if factor.kind == "talent":
        v = actor.stats.compat.talent.get(factor.index, 0)
    elif factor.kind == "abl":
        v = actor.stats.compat.abl.get(factor.index, 0)
    elif factor.kind == "palam_level":
        # PALAM level is derived from current PALAM value; placeholder
        v = actor.stats.palam.get(str(factor.index), 0)
    else:
        return 1.0

    env = {"v": v, "max": max, "min": min, "int": int}
    try:
        return float(eval(factor.expr, {"__builtins__": {}}, env))  # noqa: S307
    except (ZeroDivisionError, ValueError, SyntaxError):
        return 1.0
