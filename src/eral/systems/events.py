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
            for mark_key, min_level in event.required_marks.items():
                if scene.marks.get(mark_key, 0) < min_level:
                    break
            else:
                specificity = len(event.required_marks)
                matched.append((event.key, specificity))
                continue
            # mark check failed — skip this event
        matched.sort(key=lambda pair: -pair[1])
        return tuple(key for key, _ in matched)
