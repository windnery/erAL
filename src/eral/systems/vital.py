"""Vital statistics service: stamina, spirit, fatigue, and recovery."""

from __future__ import annotations

from dataclasses import dataclass

from eral.domain.world import CharacterState, WorldState
from eral.systems.facilities import FacilityService
from eral.systems.fatigue import calc_tired
from eral.systems.source_extra import compute_recovery_modifier


# Mapping from maxbase string keys to base integer string keys.
_MAXBASE_TO_BASE: dict[str, str] = {
    "stamina": "0",
    "spirit": "1",
    "mood": "10",
    "reason": "11",
    "anger": "12",
    "workload": "13",
    "drunkenness": "15",
    "erection": "5",
    "bladder": "4",
    "semen": "6",
    "height": "20",
    "weight": "21",
    "bust": "22",
    "waist": "23",
    "hips": "24",
}


@dataclass(slots=True)
class VitalService:
    """Orchestrates all vital-stat mutations: DOWNBASE, recovery, fatigue, and thresholds."""

    max_values: dict[str, int]
    recover_rates: dict[str, int]
    facility_service: FacilityService | None = None

    def _max_value_for_actor(self, actor: CharacterState, max_key: str) -> int:
        base_key = _MAXBASE_TO_BASE.get(max_key, max_key)
        if base_key in actor.base_caps:
            return actor.base_caps[base_key]
        return self.max_values.get(max_key, 9999)

    def _recover_rate_for_actor(self, actor: CharacterState, max_key: str) -> int:
        base_key = _MAXBASE_TO_BASE.get(max_key, max_key)
        if base_key in actor.base_recover_rates:
            return actor.base_recover_rates[base_key]
        return self.recover_rates.get(max_key, 0)

    def _recovery_mod(self, actor: CharacterState, world: WorldState | None) -> float:
        recovery_mod = compute_recovery_modifier(actor.stats)
        if world is not None and self.facility_service is not None:
            recovery_mod *= self.facility_service.recovery_multiplier(world)
        return recovery_mod

    def apply_downbase(self, actor: CharacterState, downbase: dict[str, int]) -> int:
        """Subtract DOWNBASE from BASE, accumulate fatigue. Returns fatigue increment."""
        stamina_cost = downbase.get("0", 0)
        spirit_cost = downbase.get("1", 0)

        for key, delta in downbase.items():
            current = actor.stats.base.get(key)
            new_val = max(0, current - delta)
            actor.stats.base.set(key, new_val)

        fatigue_delta = calc_tired(stamina_cost, spirit_cost)
        actor.fatigue += fatigue_delta
        return fatigue_delta

    def natural_recovery(self, actor: CharacterState, world: WorldState | None = None) -> dict[str, int]:
        """Per time-slot natural recovery and decay. Also reduces fatigue slightly."""
        recovery_mod = self._recovery_mod(actor, world)
        results: dict[str, int] = {}

        all_keys = set(self.recover_rates)
        all_keys.update(
            max_key
            for max_key, base_key in _MAXBASE_TO_BASE.items()
            if base_key in actor.base_recover_rates
        )
        for key in all_keys:
            rate = self._recover_rate_for_actor(actor, key)
            if rate == 0:
                continue
            base_key = _MAXBASE_TO_BASE.get(key, key)
            current = actor.stats.base.get(base_key)
            maximum = self._max_value_for_actor(actor, key)

            if rate > 0:
                recovery = int(rate * recovery_mod)
                new_val = min(maximum, current + recovery)
            else:
                decay = int(abs(rate) * recovery_mod)
                new_val = max(0, current - decay)

            actual = new_val - current
            if actual != 0:
                actor.stats.base.set(base_key, new_val)
                results[key] = actual

        fatigue_reduction = max(1, int(5 * recovery_mod))
        actor.fatigue = max(0, actor.fatigue - fatigue_reduction)

        return results

    def sleep_recovery(self, actor: CharacterState, world: WorldState | None = None) -> dict[str, int]:
        """Sleep recovery: major percentage of MAXBASE + significant fatigue reduction.

        Stamina recovers ~50% of max, spirit ~30% of max over a full night (8h).
        """
        recovery_mod = self._recovery_mod(actor, world)
        results: dict[str, int] = {}
        permils = {"0": 500, "1": 300}

        for base_key in ("0", "1"):
            max_key = next((k for k, v in _MAXBASE_TO_BASE.items() if v == base_key), base_key)
            current = actor.stats.base.get(base_key)
            maximum = self._max_value_for_actor(actor, max_key)
            permil = permils.get(base_key, 300)
            base_recovery = maximum * permil // 1000
            recovery = int(base_recovery * recovery_mod)
            new_val = min(maximum, current + recovery)
            actual = new_val - current
            if actual > 0:
                actor.stats.base.set(base_key, new_val)
                results[max_key] = actual

        fatigue_reduction = int(actor.fatigue * 0.8 * recovery_mod)
        actor.fatigue = max(0, actor.fatigue - max(1, fatigue_reduction))

        return results

    def rest_recovery(self, actor: CharacterState, world: WorldState | None = None) -> dict[str, int]:
        """Rest (nap) recovery: moderate percentage of MAXBASE + some fatigue reduction."""
        recovery_mod = self._recovery_mod(actor, world)
        results: dict[str, int] = {}
        permils = {"0": 200, "1": 150}

        for base_key in ("0", "1"):
            max_key = next((k for k, v in _MAXBASE_TO_BASE.items() if v == base_key), base_key)
            current = actor.stats.base.get(base_key)
            maximum = self._max_value_for_actor(actor, max_key)
            permil = permils.get(base_key, 200)
            base_recovery = maximum * permil // 1000
            recovery = int(base_recovery * recovery_mod)
            new_val = min(maximum, current + recovery)
            actual = new_val - current
            if actual > 0:
                actor.stats.base.set(base_key, new_val)
                results[max_key] = actual

        fatigue_reduction = max(5, actor.fatigue // 4)
        actor.fatigue = max(0, actor.fatigue - fatigue_reduction)

        return results

    def bathe_recovery(self, actor: CharacterState, world: WorldState | None = None) -> dict[str, int]:
        """Bath recovery: spirit-focused recovery + moderate fatigue reduction."""
        recovery_mod = self._recovery_mod(actor, world)
        results: dict[str, int] = {}
        permils = {"0": 100, "1": 250}

        for base_key in ("0", "1"):
            max_key = next((k for k, v in _MAXBASE_TO_BASE.items() if v == base_key), base_key)
            current = actor.stats.base.get(base_key)
            maximum = self._max_value_for_actor(actor, max_key)
            permil = permils.get(base_key, 100)
            base_recovery = maximum * permil // 1000
            recovery = int(base_recovery * recovery_mod)
            new_val = min(maximum, current + recovery)
            actual = new_val - current
            if actual > 0:
                actor.stats.base.set(base_key, new_val)
                results[max_key] = actual

        fatigue_reduction = max(3, actor.fatigue // 5)
        actor.fatigue = max(0, actor.fatigue - fatigue_reduction)

        return results

    def restore(
        self,
        actor: CharacterState,
        stamina: int = 0,
        spirit: int = 0,
        reduce_fatigue: int = 0,
    ) -> dict[str, int]:
        """Generic restore for items and future systems. Clamps to MAXBASE."""
        results: dict[str, int] = {}

        if stamina > 0:
            current = actor.stats.base.get("0")
            maximum = self._max_value_for_actor(actor, "stamina")
            new_val = min(maximum, current + stamina)
            actual = new_val - current
            if actual > 0:
                actor.stats.base.set("0", new_val)
                results["stamina"] = actual

        if spirit > 0:
            current = actor.stats.base.get("1")
            maximum = self._max_value_for_actor(actor, "spirit")
            new_val = min(maximum, current + spirit)
            actual = new_val - current
            if actual > 0:
                actor.stats.base.set("1", new_val)
                results["spirit"] = actual

        if reduce_fatigue > 0:
            old = actor.fatigue
            actor.fatigue = max(0, actor.fatigue - reduce_fatigue)
            results["fatigue"] = old - actor.fatigue

        return results

    def is_fainted(self, actor: CharacterState) -> bool:
        """Check if actor has fainted (stamina exhausted)."""
        return actor.stats.base.get("0") <= 0

    def is_spirit_depleted(self, actor: CharacterState) -> bool:
        """Check if actor's spirit is depleted."""
        return actor.stats.base.get("1") <= 0

    def is_decay(self, actor: CharacterState) -> bool:
        """Check if actor is in 衰弱 state: both stamina and spirit below 1/5 MAXBASE."""
        stamina = actor.stats.base.get("0")
        spirit = actor.stats.base.get("1")
        max_stamina = self._max_value_for_actor(actor, "stamina")
        max_spirit = self._max_value_for_actor(actor, "spirit")
        return stamina < max_stamina // 5 and spirit < max_spirit // 5
