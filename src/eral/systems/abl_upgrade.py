"""ABL upgrade system with eraTW multi-route semantics."""

from __future__ import annotations

from eral.content.abl_upgrade import AblDefinition, AblUpgradeConfig
from eral.domain.stats import ActorNumericState

TALENT_LOVE = 15
TALENT_OATH = 16


def _compute_explv_level(exp_value: int, explv: tuple[int, ...]) -> int:
    """Return highest level where explv[level] <= exp_value."""
    level = 0
    for i, threshold in enumerate(explv):
        if exp_value >= threshold:
            level = i
        else:
            break
    return level


def _max_level(talent_state, config: AblUpgradeConfig) -> int:
    """Determine ABL level cap based on TALENT."""
    if talent_state.get(TALENT_OATH) > 0:
        return config.max_level_with_oath
    if talent_state.get(TALENT_LOVE) > 0:
        return config.max_level_with_love
    return config.max_level_without_love


def _can_upgrade(
    stats: ActorNumericState,
    definition: AblDefinition,
    current_level: int,
    config: AblUpgradeConfig,
    aptitude_offset: int,
) -> tuple[bool, int | None, dict[str, int]]:
    """Check whether any route is viable. Returns (success, juel_key, demand)."""
    if definition.upgrade_mode == "exp_direct":
        if definition.exp_direct_key is None:
            return False, None, {}
        explv_index = current_level + definition.exp_direct_offset - aptitude_offset
        explv_index = max(0, min(explv_index, len(config.explv) - 1))
        need_exp = config.explv[explv_index]
        need_exp = max(1, int(need_exp / definition.rate))
        actual_exp = stats.exp.get(definition.exp_direct_key)
        return actual_exp >= need_exp, None, {}

    # juel_exp mode: evaluate routes
    for route_idx, route in enumerate(definition.routes):
        # Ensure every JUEL table in this route is long enough
        if any(current_level >= len(table) for table in route.juel_costs.values()):
            continue

        # Compute discounted demand for each JUEL type in the route
        demands: dict[str, int] = {}
        route_viable = True
        for juel_key, juel_table in route.juel_costs.items():
            base_demand = juel_table[current_level]
            demand = max(1, int(base_demand / definition.rate))

            # Apply dynamic discounts
            for discount in route.discount_factors:
                exp_value = stats.exp.get(discount.exp_key)
                exp_level = _compute_explv_level(exp_value, config.explv)
                numerator = discount.numerator + discount.level_numerator_offset * current_level
                denominator = discount.denominator_offset + exp_level
                if denominator <= 0:
                    denominator = 1
                demand = demand * numerator // denominator

            if stats.juel.get(juel_key) < demand:
                route_viable = False
                break
            demands[juel_key] = demand

        if not route_viable:
            continue

        # Check EXP requirements
        for exp_key, required_table in route.exp_requirements.items():
            required = required_table[min(current_level, len(required_table) - 1)]
            if stats.exp.get(exp_key) < required:
                route_viable = False
                break
        if not route_viable:
            continue

        return True, route_idx, demands

    return False, None, {}


def _apply_upgrade(
    stats: ActorNumericState,
    definition: AblDefinition,
    current_level: int,
    route_idx: int | None,
    demands: dict[str, int],
) -> int:
    """Deduct resources and raise ABL. Returns new level."""
    new_level = current_level + 1
    stats.compat.abl.set(definition.abl_index, new_level)

    if definition.upgrade_mode == "juel_exp" and route_idx is not None:
        for juel_key, demand in demands.items():
            stats.juel.add(juel_key, -demand)

    return new_level


def check_and_apply_abl_upgrades(
    stats: ActorNumericState,
    config: AblUpgradeConfig,
    aptitude_offset: int = 0,
) -> list[tuple[int, int, int]]:
    """Check each ABL for automatic level-ups. Returns list of (abl_index, old_level, new_level).

    Silent skip if resources are insufficient. Evaluated in definition order.
    """
    results: list[tuple[int, int, int]] = []
    max_lv = _max_level(stats.compat.talent, config)

    for definition in config.definitions:
        current_level = stats.compat.abl.get(definition.abl_index)
        if current_level >= max_lv:
            continue

        # Check cross-ABL requirements
        reqs_ok = True
        for req in definition.requirements:
            req_level = stats.compat.abl.get(req.abl_index)
            if req_level < current_level + req.min_level_offset:
                reqs_ok = False
                break
        if not reqs_ok:
            continue

        viable, route_idx, demands = _can_upgrade(
            stats, definition, current_level, config, aptitude_offset,
        )
        if viable:
            new_level = _apply_upgrade(stats, definition, current_level, route_idx, demands)
            results.append((definition.abl_index, current_level, new_level))

    return results
