"""Port facility upgrade and effect query service."""

from __future__ import annotations

from dataclasses import dataclass

from eral.content.facilities import FacilityDefinition, FacilityEffect
from eral.domain.world import WorldState
from eral.systems.wallet import WalletService


@dataclass(slots=True)
class FacilityService:
    """Manage facility upgrades and provide effect queries."""

    definitions: tuple[FacilityDefinition, ...]
    wallet: WalletService | None = None

    def _definition(self, facility_key: str) -> FacilityDefinition | None:
        for d in self.definitions:
            if d.key == facility_key:
                return d
        return None

    def get_level(self, world: WorldState, facility_key: str) -> int:
        return world.facility_levels.get(facility_key, 0)

    def get_upgrade_cost(self, facility_key: str, current_level: int) -> int | None:
        definition = self._definition(facility_key)
        if definition is None or current_level >= definition.max_level:
            return None
        if current_level >= len(definition.upgrade_costs):
            return None
        return definition.upgrade_costs[current_level]

    def upgrade(self, world: WorldState, facility_key: str) -> bool:
        definition = self._definition(facility_key)
        if definition is None:
            return False
        current = self.get_level(world, facility_key)
        if current >= definition.max_level:
            return False
        if current >= len(definition.upgrade_costs):
            return False
        cost = definition.upgrade_costs[current]
        if self.wallet is None:
            return False
        if not self.wallet.spend_port(world, cost, reason="facility_upgrade", source_key=facility_key):
            return False
        world.facility_levels[facility_key] = current + 1
        return True

    def total_effect(self, world: WorldState, effect_type: str) -> dict[str, int | float | str]:
        """Aggregate all active effects of a given type across all facilities.

        For numeric params, sums values. For string params, collects into a list under the same key.
        """
        result: dict[str, int | float | list[str]] = {}
        for definition in self.definitions:
            level = self.get_level(world, definition.key)
            for effect in definition.effects:
                if effect.type != effect_type or level < effect.min_level:
                    continue
                for k, v in effect.params.items():
                    if isinstance(v, str):
                        existing = result.get(k)
                        if isinstance(existing, list):
                            existing.append(v)
                        else:
                            result[k] = [v]
                    else:
                        result[k] = result.get(k, 0) + v
        return result

    def recovery_multiplier(self, world: WorldState) -> float:
        """Sum of all boost_recovery multipliers, plus 1.0 base."""
        aggregated = self.total_effect(world, "boost_recovery")
        return 1.0 + float(aggregated.get("multiplier", 0))

    def income_multiplier(self, world: WorldState) -> float:
        """Sum of all boost_income multipliers, plus 1.0 base."""
        aggregated = self.total_effect(world, "boost_income")
        return 1.0 + float(aggregated.get("multiplier", 0))

    def relation_multiplier(self, world: WorldState) -> float:
        """Sum of all boost_relation multipliers, plus 1.0 base."""
        aggregated = self.total_effect(world, "boost_relation")
        return 1.0 + float(aggregated.get("multiplier", 0))
