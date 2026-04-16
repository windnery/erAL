"""Minimal map movement utilities."""

from __future__ import annotations

from dataclasses import dataclass

from eral.domain.actions import ActionResult
from eral.domain.map import PortMap
from eral.domain.world import PortLocation, WorldState
from eral.engine.events import EventBus
from eral.engine.runtime_logger import RuntimeLogger
from eral.systems.companions import CompanionService
from eral.systems.time_service import TimeService


@dataclass(slots=True)
class NavigationService:
    """Move the player between connected locations."""

    port_map: PortMap
    companion_service: CompanionService | None = None
    event_bus: EventBus | None = None
    runtime_logger: RuntimeLogger | None = None
    time_service: TimeService | None = None

    def can_see_private(self, world: WorldState) -> bool:
        """Whether the player can currently see private locations.

        Private locations are visible when the player is following or
        on a date with a character — i.e. the character grants access
        to their private space.
        """
        for actor in world.characters:
            if actor.is_following or actor.is_on_date:
                return True
        return False

    def visible_destinations(self, world: WorldState) -> tuple[str, ...]:
        """Return neighbor keys the player can navigate to."""
        return self.port_map.visible_neighbors(
            world.active_location.key,
            can_see_private=self.can_see_private(world),
        )

    def move_player(self, world: WorldState, destination_key: str) -> ActionResult:
        if destination_key == world.active_location.key:
            return ActionResult(
                action_key="move",
                messages=["已经在目的地了。"],
            )

        visible = self.visible_destinations(world)
        if destination_key not in visible:
            # Also check structural neighbors — if reachable but not visible, give a clearer message
            neighbors = self.port_map.neighbors_of(world.active_location.key)
            if destination_key in neighbors:
                raise ValueError(
                    f"目前无法前往{self.port_map.location_by_key(destination_key).display_name}。"
                )
            raise ValueError(
                f"{destination_key} is not reachable from {world.active_location.key}."
            )

        destination = self.port_map.location_by_key(destination_key)
        world.active_location = PortLocation(
            key=destination.key,
            display_name=destination.display_name,
        )
        if self.time_service is not None:
            self.time_service.advance_minutes(world, 15)
        if self.companion_service is not None:
            self.companion_service.move_followers(world, destination.key)

        # Mark encounter state for non-following characters at destination
        encountered: list[str] = []
        for actor in world.characters:
            if actor.is_following:
                continue
            if actor.location_key == destination.key:
                if actor.encounter_location_key != destination.key:
                    encountered.append(actor.key)
                actor.encounter_location_key = destination.key

        messages = [f"前往了{destination.display_name}。"]
        if encountered:
            for key in encountered:
                actor = next(c for c in world.characters if c.key == key)
                messages.append(f"遇到了{actor.display_name}。")
            if self.event_bus is not None:
                self.event_bus.publish(
                    "encounter",
                    location_key=destination.key,
                    actor_keys=encountered,
                )
        if self.runtime_logger is not None:
            self.runtime_logger.append(
                kind="move",
                action_key="move",
                day=world.current_day,
                time_slot=world.current_time_slot.value,
                location_key=destination.key,
                actor_key=None,
                triggered_events=[],
            )

        return ActionResult(
            action_key="move",
            messages=messages,
        )
