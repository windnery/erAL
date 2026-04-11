"""Coarse-grained NPC schedule refresh."""

from __future__ import annotations

from dataclasses import dataclass

from eral.content.characters import CharacterDefinition
from eral.domain.world import WorldState


@dataclass(slots=True)
class ScheduleService:
    """Refresh actor locations from static time-slot schedules."""

    roster: dict[str, CharacterDefinition]

    def refresh_world(self, world: WorldState) -> None:
        slot_key = world.current_time_slot.value
        for actor in world.characters:
            if actor.is_following or actor.is_on_date:
                continue
            definition = self.roster.get(actor.key)
            if not definition:
                continue
            actor.previous_location_key = actor.location_key
            new_location = definition.schedule.get(slot_key, actor.location_key)
            if new_location != actor.location_key:
                actor.encounter_location_key = None
            actor.location_key = new_location
