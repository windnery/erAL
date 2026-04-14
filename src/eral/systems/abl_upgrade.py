"""ABL upgrade system: check and apply level-ups based on accumulated experience."""

from __future__ import annotations

from eral.content.abl_upgrade import AblUpgradeConfig


def compute_demand(
    abl_index: int,
    current_level: int,
    aptitude_offset: int,
    config: AblUpgradeConfig,
) -> int:
    abl_def = None
    for d in config.definitions:
        if d.abl_index == abl_index:
            abl_def = d
            break

    if abl_def is None:
        rate = config.default_rate
    else:
        rate = abl_def.rate

    target_level = current_level + 1
    target_index = max(0, target_level - aptitude_offset)

    if target_index >= len(config.explv):
        base_exp = config.explv[-1]
    elif target_index < 0:
        base_exp = config.explv[0]
    else:
        base_exp = config.explv[target_index]

    demand = max(1, int(base_exp * config.default_rate / rate))
    return demand


def check_and_apply_abl_upgrades(
    stats: "ActorNumericState",
    config: AblUpgradeConfig,
    aptitude_offset: int = 0,
) -> list[tuple[int, int, int]]:
    """Check each ABL for level-ups. Returns list of (abl_index, old_level, new_level).

    Accumulates abl_* SOURCE into persistent abl_exp, then checks for upgrades.
    """
    results: list[tuple[int, int, int]] = []

    for definition in config.definitions:
        # Accumulate SOURCE abl experience into persistent store
        experience_key = f"abl_{definition.abl_index}"
        source_exp = stats.source.get(experience_key)
        if source_exp > 0:
            stats.abl_exp[definition.abl_index] = (
                stats.abl_exp.get(definition.abl_index, 0) + source_exp
            )

        current_level = stats.compat.abl.get(definition.abl_index)
        if current_level >= len(config.explv) - 1:
            continue

        accumulated = stats.abl_exp.get(definition.abl_index, 0)
        if accumulated == 0:
            continue

        demand = compute_demand(
            definition.abl_index, current_level, aptitude_offset, config,
        )

        if accumulated >= demand:
            new_level = current_level + 1
            stats.compat.abl.set(definition.abl_index, new_level)
            stats.abl_exp[definition.abl_index] = accumulated - demand
            results.append((definition.abl_index, current_level, new_level))

    return results
