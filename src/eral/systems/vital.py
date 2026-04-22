"""Vital statistics service: stamina, spirit, fatigue, and recovery."""

from __future__ import annotations

from dataclasses import dataclass

from eral.content.talent_effects import TalentEffect
from eral.domain.world import CharacterState, WorldState
from eral.systems.facilities import FacilityService
from eral.systems.fatigue import calc_tired
from eral.systems.source_extra import compute_recovery_modifier


@dataclass(slots=True)
class VitalService:
    """Orchestrates all vital-stat mutations: DOWNBASE, recovery, fatigue, and thresholds."""

    max_values: dict[str, int]
    recover_rates: dict[str, int]
    talent_effects: tuple[TalentEffect, ...] = ()
    facility_service: FacilityService | None = None

    def _recovery_mod(self, actor: CharacterState, world: WorldState | None) -> float:
        recovery_mod = compute_recovery_modifier(actor.stats, self.talent_effects)
        if world is not None and self.facility_service is not None:
            recovery_mod *= self.facility_service.recovery_multiplier(world)
        return recovery_mod

    def apply_downbase(self, actor: CharacterState, downbase: dict[str, int]) -> int:
        """Subtract DOWNBASE from BASE, accumulate fatigue. Returns fatigue increment."""
        stamina_cost = downbase.get("stamina", 0)
        spirit_cost = downbase.get("spirit", 0)

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

        for key, rate in self.recover_rates.items():
            if rate == 0:
                continue
            current = actor.stats.base.get(key)
            maximum = self.max_values.get(key, 9999)

            if rate > 0:
                recovery = int(rate * recovery_mod)
                new_val = min(maximum, current + recovery)
            else:
                decay = int(abs(rate) * recovery_mod)
                new_val = max(0, current - decay)

            actual = new_val - current
            if actual != 0:
                actor.stats.base.set(key, new_val)
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
        permils = {"stamina": 500, "spirit": 300}

        for key in ("stamina", "spirit"):
            current = actor.stats.base.get(key)
            maximum = self.max_values.get(key, 2000)
            permil = permils.get(key, 300)
            base_recovery = maximum * permil // 1000
            recovery = int(base_recovery * recovery_mod)
            new_val = min(maximum, current + recovery)
            actual = new_val - current
            if actual > 0:
                actor.stats.base.set(key, new_val)
                results[key] = actual

        fatigue_reduction = int(actor.fatigue * 0.8 * recovery_mod)
        actor.fatigue = max(0, actor.fatigue - max(1, fatigue_reduction))

        return results

    def rest_recovery(self, actor: CharacterState, world: WorldState | None = None) -> dict[str, int]:
        """Rest (nap) recovery: moderate percentage of MAXBASE + some fatigue reduction."""
        recovery_mod = self._recovery_mod(actor, world)
        results: dict[str, int] = {}
        permils = {"stamina": 200, "spirit": 150}

        for key in ("stamina", "spirit"):
            current = actor.stats.base.get(key)
            maximum = self.max_values.get(key, 2000)
            permil = permils.get(key, 200)
            base_recovery = maximum * permil // 1000
            recovery = int(base_recovery * recovery_mod)
            new_val = min(maximum, current + recovery)
            actual = new_val - current
            if actual > 0:
                actor.stats.base.set(key, new_val)
                results[key] = actual

        fatigue_reduction = max(5, actor.fatigue // 4)
        actor.fatigue = max(0, actor.fatigue - fatigue_reduction)

        return results

    def bathe_recovery(self, actor: CharacterState, world: WorldState | None = None) -> dict[str, int]:
        """Bath recovery: spirit-focused recovery + moderate fatigue reduction."""
        recovery_mod = self._recovery_mod(actor, world)
        results: dict[str, int] = {}
        permils = {"stamina": 100, "spirit": 250}

        for key in ("stamina", "spirit"):
            current = actor.stats.base.get(key)
            maximum = self.max_values.get(key, 2000)
            permil = permils.get(key, 100)
            base_recovery = maximum * permil // 1000
            recovery = int(base_recovery * recovery_mod)
            new_val = min(maximum, current + recovery)
            actual = new_val - current
            if actual > 0:
                actor.stats.base.set(key, new_val)
                results[key] = actual

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
            current = actor.stats.base.get("stamina")
            maximum = self.max_values.get("stamina", 2000)
            new_val = min(maximum, current + stamina)
            actual = new_val - current
            if actual > 0:
                actor.stats.base.set("stamina", new_val)
                results["stamina"] = actual

        if spirit > 0:
            current = actor.stats.base.get("spirit")
            maximum = self.max_values.get("spirit", 1500)
            new_val = min(maximum, current + spirit)
            actual = new_val - current
            if actual > 0:
                actor.stats.base.set("spirit", new_val)
                results["spirit"] = actual

        if reduce_fatigue > 0:
            old = actor.fatigue
            actor.fatigue = max(0, actor.fatigue - reduce_fatigue)
            results["fatigue"] = old - actor.fatigue

        return results

    def is_fainted(self, actor: CharacterState) -> bool:
        """Check if actor has fainted (stamina exhausted)."""
        return actor.stats.base.get("stamina") <= 0

    def is_spirit_depleted(self, actor: CharacterState) -> bool:
        """Check if actor's spirit is depleted."""
        return actor.stats.base.get("spirit") <= 0

    def is_decay(self, actor: CharacterState) -> bool:
        """Check if actor is in 衰弱 state: both stamina and spirit below 1/5 MAXBASE."""
        stamina = actor.stats.base.get("stamina")
        spirit = actor.stats.base.get("spirit")
        max_stamina = self.max_values.get("stamina", 2000)
        max_spirit = self.max_values.get("spirit", 1500)
        return stamina < max_stamina // 5 and spirit < max_spirit // 5