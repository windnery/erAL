"""Scene context builder."""

from __future__ import annotations

from dataclasses import dataclass

from eral.domain.scene import SceneContext
from eral.domain.world import CharacterState, WorldState


@dataclass(slots=True)
class SceneService:
    """Build scene context from current world state."""

    def build_for_actor(
        self,
        world: WorldState,
        actor: CharacterState,
        action_key: str,
        location_tags: tuple[str, ...],
    ) -> SceneContext:
        visible_characters = world.visible_characters()
        is_private = len(visible_characters) <= 1
        return SceneContext(
            actor_key=actor.key,
            actor_tags=actor.tags,
            action_key=action_key,
            current_day=world.current_day,
            time_slot=world.current_time_slot.value,
            location_key=world.active_location.key,
            location_tags=location_tags,
            affection=actor.affection,
            trust=actor.trust,
            obedience=actor.obedience,
            relationship_stage=(
                actor.relationship_stage.key if actor.relationship_stage is not None else "stranger"
            ),
            relationship_rank=(
                actor.relationship_stage.rank if actor.relationship_stage is not None else 0
            ),
            is_following=actor.is_following,
            is_on_date=actor.is_on_date,
            is_same_room=actor.is_same_room,
            visible_count=len(visible_characters),
            is_private=is_private,
            marks=dict(actor.marks),
        )
