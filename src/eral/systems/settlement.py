"""Unified SOURCE settlement pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from eral.content.settlement import SettlementRule
from eral.content.stat_axes import AxisFamily
from eral.domain.actions import AppliedChange
from eral.domain.world import CharacterState, WorldState
from eral.systems.relationships import RelationshipService


@dataclass(slots=True)
class SettlementService:
    """Apply SOURCE values into named blocks and era-compat state."""

    rules: tuple[SettlementRule, ...]
    relationship_service: RelationshipService | None = None

    def settle_actor(self, world: WorldState, actor: CharacterState) -> list[AppliedChange]:
        changes: list[AppliedChange] = []

        for rule in self.rules:
            source_value = actor.stats.source.get(rule.source)
            if source_value == 0:
                continue

            delta = source_value * rule.scale
            target_family = rule.target_family

            if target_family == AxisFamily.BASE and rule.target_key:
                before = actor.stats.base.get(rule.target_key)
                after = actor.stats.base.add(rule.target_key, delta)
                changes.append(AppliedChange("base", rule.target_key, before, after, delta))
            elif target_family == AxisFamily.PALAM and rule.target_key:
                before = actor.stats.palam.get(rule.target_key)
                after = actor.stats.palam.add(rule.target_key, delta)
                changes.append(AppliedChange("palam", rule.target_key, before, after, delta))
            elif target_family == AxisFamily.CFLAG and rule.target_index is not None:
                before = actor.stats.compat.cflag.get(rule.target_index)
                after = actor.stats.compat.cflag.add(rule.target_index, delta)
                changes.append(
                    AppliedChange("cflag", str(rule.target_index), before, after, delta)
                )
            elif target_family == AxisFamily.TFLAG and rule.target_index is not None:
                before = world.compat.tflag.get(rule.target_index)
                after = world.compat.tflag.add(rule.target_index, delta)
                changes.append(
                    AppliedChange("tflag", str(rule.target_index), before, after, delta)
                )

        actor.sync_derived_fields()
        if self.relationship_service is not None:
            self.relationship_service.update_actor(actor)
        actor.stats.clear_source()
        return changes
