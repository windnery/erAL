"""Lightweight map distribution helpers."""

from __future__ import annotations

from dataclasses import dataclass

from eral.domain.world import CharacterState, WorldState


@dataclass(slots=True)
class DistributionService:
    """Resolve which characters are currently present at one location."""

    def present_characters(self, world: WorldState, location_key: str) -> tuple[CharacterState, ...]:
        return tuple(
            actor
            for actor in sorted(world.characters, key=self._sort_key, reverse=True)
            if actor.location_key == location_key and not actor.is_on_commission
        )

    @staticmethod
    def _sort_key(actor: CharacterState) -> tuple[int, int, int, str]:
        interaction_priority = 1 if actor.tags and ("shopkeeper" in actor.tags or "service_npc" in actor.tags) else 0
        relationship_priority = actor.affection + actor.trust
        return (interaction_priority, relationship_priority, actor.obedience, actor.key)
