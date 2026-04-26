"""Fatigue calculation and recovery system.

Implements:
- CULC_TIRED: nonlinear fatigue from stamina/spirit expenditure
- Natural recovery per time slot
- Sleep recovery with recovery speed modifier
- Decay (衰弱) state detection
"""

from __future__ import annotations

import math

from eral.domain.stats import ActorNumericState
from eral.systems.source_extra import compute_recovery_modifier

# Mapping from maxbase string keys to base integer string keys.
_MAXBASE_TO_BASE: dict[str, str] = {
    "stamina": "0",
    "spirit": "1",
}


def calc_tired(downbase_stamina: int, downbase_spirit: int) -> int:
    """Compute nonlinear fatigue from DOWNBASE values.

    eraTW formula: CULC_TIRED(x) = 0 if x < 10, else t * sqrt(t) where t = x/10.

    The combined fatigue is:
        ADD_TIRED = 12 * CULC_TIRED(stamina) + 8 * CULC_TIRED(spirit)
    """
    stamina_tired = _culc_tired(downbase_stamina)
    spirit_tired = _culc_tired(downbase_spirit)
    return 12 * stamina_tired + 8 * spirit_tired


def _culc_tired(value: int) -> int:
    if value < 10:
        return 0
    t = value / 10.0
    return int(t * math.sqrt(t))


def apply_natural_recovery(
    stats: ActorNumericState,
    maxbase: dict[str, int],
    hours: float = 1.0,
) -> dict[str, int]:
    """Natural recovery for a time slot.

    eraTW: stamina_recovery = (10 + recovery_speed) * Lapse / 20
           spirit_recovery = (10 + recovery_speed) * Lapse / 20

    Returns dict of stat_key -> amount_recovered.
    """
    recovery_mod = compute_recovery_modifier(stats)

    results: dict[str, int] = {}
    for max_key, base_key in _MAXBASE_TO_BASE.items():
        current = stats.base.get(base_key)
        maximum = maxbase.get(max_key, 2000)
        base_recovery = int((10 * hours) / 20)
        recovery = int(base_recovery * recovery_mod)
        new_val = min(maximum, current + recovery)
        actual = new_val - current
        if actual > 0:
            stats.base.set(base_key, new_val)
            results[max_key] = actual

    return results


def apply_sleep_recovery(
    stats: ActorNumericState,
    maxbase: dict[str, int],
    hours: float = 8.0,
) -> dict[str, int]:
    """Sleep recovery: recovers a percentage of MAXBASE.

    eraTW: stamina_recovery = MAXBASE * permil / 1000, modified by recovery_speed.
    Normal sleep: permil ~= 500 (50% of MAXBASE over 8 hours).
    """
    recovery_mod = compute_recovery_modifier(stats)

    results: dict[str, int] = {}
    for max_key, base_key in _MAXBASE_TO_BASE.items():
        current = stats.base.get(base_key)
        maximum = maxbase.get(max_key, 2000)
        permil = int(500 * hours / 8)
        base_recovery = maximum * permil // 1000
        recovery = int(base_recovery * recovery_mod)
        new_val = min(maximum, current + recovery)
        actual = new_val - current
        if actual > 0:
            stats.base.set(base_key, new_val)
            results[max_key] = actual

    return results


def is_decay_state(stats: ActorNumericState, maxbase: dict[str, int]) -> bool:
    """Check if actor is in 衰弱 (decay) state.

    衰弱 occurs when both stamina and spirit are below 1/5 of MAXBASE.
    """
    stamina = stats.base.get("0")
    spirit = stats.base.get("1")
    max_stamina = maxbase.get("stamina", 2000)
    max_spirit = maxbase.get("spirit", 1500)
    return stamina < max_stamina // 5 and spirit < max_spirit // 5