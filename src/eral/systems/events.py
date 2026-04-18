"""Lightweight event trigger matching."""

from __future__ import annotations

from dataclasses import dataclass

from eral.content.events import EventDefinition
from eral.domain.scene import SceneContext
from eral.systems.relationships import RelationshipService


@dataclass(slots=True)
class EventService:
    """Resolve events from scene context and action key."""

    events: tuple[EventDefinition, ...]
    relationship_service: RelationshipService

    def triggered_events(self, scene: SceneContext) -> tuple[str, ...]:
        matched: list[tuple[str, int]] = []
        for event in self.events:
            if event.action_key != scene.action_key:
                continue
            if event.actor_tags and not any(tag in scene.actor_tags for tag in event.actor_tags):
                continue
            if event.location_keys and scene.location_key not in event.location_keys:
                continue
            if event.time_slots and scene.time_slot not in event.time_slots:
                continue
            if event.seasons and scene.season not in event.seasons:
                continue
            if event.min_affection is not None and scene.affection < event.min_affection:
                continue
            if event.min_trust is not None and scene.trust < event.min_trust:
                continue
            if event.min_obedience is not None and scene.obedience < event.min_obedience:
                continue
            if event.required_stage is not None:
                required_rank = self.relationship_service.rank_of(event.required_stage)
                if scene.relationship_rank < required_rank:
                    continue
            if event.requires_date is not None and scene.is_on_date != event.requires_date:
                continue
            if event.requires_private and not scene.is_private:
                continue
            if event.required_skin_key is not None and scene.equipped_skin_key != event.required_skin_key:
                continue
            if event.required_skin_tags and not all(
                tag in scene.equipped_skin_tags for tag in event.required_skin_tags
            ):
                continue
            if event.required_removed_slots and not all(
                slot in scene.removed_slots for slot in event.required_removed_slots
            ):
                continue
            if event.forbidden_removed_slots and any(
                slot in scene.removed_slots for slot in event.forbidden_removed_slots
            ):
                continue
            if event.requires_training is not None and scene.is_training != event.requires_training:
                continue
            if event.required_training_results and not all(
                r in scene.training_results for r in event.required_training_results
            ):
                continue
            for mark_key, min_level in event.required_marks.items():
                if scene.marks.get(mark_key, 0) < min_level:
                    break
            else:
                specificity = (
                    len(event.required_marks)
                    + len(event.required_skin_tags)
                    + len(event.required_removed_slots)
                    + len(event.forbidden_removed_slots)
                    + (1 if event.required_skin_key is not None else 0)
                    + (1 if event.required_stage is not None else 0)
                )
                matched.append((event.key, specificity))
                continue
            # mark check failed — skip this event
        matched.sort(key=lambda pair: -pair[1])
        return tuple(key for key, _ in matched)
