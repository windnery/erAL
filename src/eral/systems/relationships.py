"""Relationship stage resolution."""

from __future__ import annotations

from dataclasses import dataclass

from eral.content.relationships import RelationshipStageDefinition
from eral.domain.relationship import RelationshipStage
from eral.domain.world import CharacterState, WorldState


@dataclass(slots=True)
class RelationshipService:
    """Resolve relationship stages from affection and trust."""

    stages: tuple[RelationshipStageDefinition, ...]

    def update_actor(self, actor: CharacterState) -> None:
        actor.relationship_stage = self.resolve_stage(actor.affection, actor.trust)

    def refresh_world(self, world: WorldState) -> None:
        for actor in world.characters:
            self.update_actor(actor)

    def resolve_stage(self, affection: int, trust: int) -> RelationshipStage:
        chosen_index = 0
        for index, stage in enumerate(self.stages):
            if affection >= stage.min_affection and trust >= stage.min_trust:
                chosen_index = index
        chosen = self.stages[chosen_index]
        return RelationshipStage(
            key=chosen.key,
            display_name=chosen.display_name,
            rank=chosen_index,
        )

    def rank_of(self, stage_key: str) -> int:
        for index, stage in enumerate(self.stages):
            if stage.key == stage_key:
                return index
        raise KeyError(stage_key)
