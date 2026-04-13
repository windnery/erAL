"""Relationship stage resolution."""

from __future__ import annotations

from dataclasses import dataclass

from eral.content.relationships import RelationshipStageDefinition
from eral.domain.relationship import RelationshipStage
from eral.domain.world import CharacterState, WorldState

ABL_INTIMACY_INDEX = 12


@dataclass(slots=True)
class RelationshipService:
    """Resolve relationship stages from affection, trust, intimacy, and marks."""

    stages: tuple[RelationshipStageDefinition, ...]

    def update_actor(self, actor: CharacterState) -> None:
        actor.relationship_stage = self.resolve_stage(actor)

    def refresh_world(self, world: WorldState) -> None:
        for actor in world.characters:
            self.update_actor(actor)

    def resolve_stage_from_stats(self, affection: int, trust: int, intimacy: int = 0, has_dislike_mark: bool = False) -> RelationshipStage:
        chosen_index = 0
        for index, stage in enumerate(self.stages):
            if affection >= stage.min_affection and trust >= stage.min_trust:
                if intimacy >= stage.min_intimacy:
                    if stage.no_dislike_mark and has_dislike_mark:
                        continue
                    chosen_index = index
        chosen = self.stages[chosen_index]
        return RelationshipStage(
            key=chosen.key,
            display_name=chosen.display_name,
            rank=chosen_index,
        )

    def resolve_stage(self, actor: CharacterState) -> RelationshipStage:
        intimacy = actor.stats.compat.abl.get(ABL_INTIMACY_INDEX)
        has_dislike_mark = actor.has_mark("dislike_mark")
        return self.resolve_stage_from_stats(
            affection=actor.affection,
            trust=actor.trust,
            intimacy=intimacy,
            has_dislike_mark=has_dislike_mark,
        )

    def rank_of(self, stage_key: str) -> int:
        for index, stage in enumerate(self.stages):
            if stage.key == stage_key:
                return index
        raise KeyError(stage_key)