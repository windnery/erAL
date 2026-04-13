"""Date flow built on top of follow state."""

from __future__ import annotations

from dataclasses import dataclass

from eral.domain.compat_semantics import CFLAGKey, actor_cflag
from eral.domain.world import CharacterState, WorldState
from eral.systems.companions import CompanionService


@dataclass(slots=True)
class DateService:
    """Manage date state using eraTW-like ongoing-date semantics."""

    companion_service: CompanionService

    def refresh_world(self, world: WorldState) -> None:
        world.date_partner_key = None
        for actor in world.characters:
            actor_cflag.set(actor, CFLAGKey.ON_DATE, 1 if actor.is_on_date else 0)
            if actor.is_on_date:
                world.date_partner_key = actor.key

    def start_date(self, world: WorldState, actor: CharacterState) -> None:
        if not actor.is_following:
            self.companion_service.start_follow(world, actor)
        actor.is_on_date = True
        self.refresh_world(world)
        self.companion_service.refresh_world(world)

    def end_date(self, world: WorldState, actor: CharacterState) -> None:
        actor.is_on_date = False
        self.refresh_world(world)
        self.companion_service.refresh_world(world)

