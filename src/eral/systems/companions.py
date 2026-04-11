"""Follow and same-room state management inspired by eraTW semantics."""

from __future__ import annotations

from dataclasses import dataclass

from eral.domain.world import CharacterState, WorldState


@dataclass(slots=True)
class CompanionService:
    """Manage follow, same-room, and encounter-style state."""

    def refresh_world(self, world: WorldState) -> None:
        for actor in world.characters:
            actor.is_same_room = actor.location_key == world.active_location.key
            actor.stats.compat.cflag.set(319, 1 if actor.is_same_room else 0)
            actor.stats.compat.cflag.set(320, 1 if actor.is_following else 0)
            actor.stats.compat.cflag.set(329, 1 if actor.follow_ready else 0)

    def start_follow(self, world: WorldState, actor: CharacterState) -> None:
        actor.follow_ready = True
        actor.is_following = True
        actor.encounter_location_key = world.active_location.key
        self.refresh_world(world)

    def stop_follow(self, world: WorldState, actor: CharacterState) -> None:
        actor.follow_ready = False
        actor.is_following = False
        actor.is_on_date = False
        self.refresh_world(world)

    def move_followers(self, world: WorldState, destination_key: str) -> None:
        for actor in world.characters:
            if not actor.is_following:
                continue
            actor.previous_location_key = actor.location_key
            actor.location_key = destination_key
            actor.encounter_location_key = destination_key
        self.refresh_world(world)
