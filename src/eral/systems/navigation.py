"""Navigation service with shortest-path support."""

from __future__ import annotations

from dataclasses import dataclass

from eral.domain.actions import ActionResult
from eral.domain.map import PathResult, PortMap
from eral.domain.world import PortLocation, WorldState
from eral.engine.events import EventBus
from eral.engine.runtime_logger import RuntimeLogger
from eral.systems.companions import CompanionService
from eral.systems.distribution import DistributionService
from eral.systems.time_service import TimeService


@dataclass(frozen=True, slots=True)
class MovePlan:
    """UI-agnostic move plan — can be rendered by any UI layer.

    All fields are plain data; no formatting or presentation logic here.
    Future renderers (CLI, Web, TUI) consume this structure directly.
    """

    destination_key: str
    destination_name: str
    destination_area_key: str
    destination_area_name: str
    path: tuple[str, ...]
    total_cost_minutes: int
    is_adjacent: bool


@dataclass(slots=True)
class NavigationService:
    """Move the player between locations using shortest-path routing."""

    port_map: PortMap
    companion_service: CompanionService | None = None
    distribution_service: DistributionService | None = None
    event_bus: EventBus | None = None
    runtime_logger: RuntimeLogger | None = None
    time_service: TimeService | None = None

    def can_see_private(self, world: WorldState) -> bool:
        """Whether the player can currently see private locations."""
        for actor in world.characters:
            if actor.is_following or actor.is_on_date:
                return True
        return False

    def plan_move(self, world: WorldState, destination_key: str) -> MovePlan | None:
        """Plan a move without executing it. Returns None if unreachable."""
        result = self.port_map.shortest_path(
            world.active_location.key, destination_key,
        )
        if result is None:
            return None
        # Re-check visibility on the destination
        dest_loc = self.port_map.location_by_key(destination_key)
        if dest_loc.visibility == "hidden":
            return None
        if dest_loc.visibility == "private" and not self.can_see_private(world):
            return None
        area = self.port_map.area_by_key(dest_loc.area_key) if dest_loc.area_key else None
        return MovePlan(
            destination_key=destination_key,
            destination_name=dest_loc.display_name,
            destination_area_key=dest_loc.area_key,
            destination_area_name=area.display_name if area else "",
            path=result.path,
            total_cost_minutes=result.total_cost,
            is_adjacent=(result.hop_count <= 1),
        )

    def available_destinations(self, world: WorldState) -> list[MovePlan]:
        """All reachable destinations grouped for display.

        Returns structured data — any UI layer can render this as
        a numbered list, a clickable map, or a tree view.
        """
        reachable = self.port_map.reachable_destinations(
            world.active_location.key,
            can_see_private=self.can_see_private(world),
        )
        plans: list[MovePlan] = []
        for dest_key, path_result in reachable.items():
            dest_loc = self.port_map.location_by_key(dest_key)
            area = self.port_map.area_by_key(dest_loc.area_key) if dest_loc.area_key else None
            plans.append(MovePlan(
                destination_key=dest_key,
                destination_name=dest_loc.display_name,
                destination_area_key=dest_loc.area_key,
                destination_area_name=area.display_name if area else "",
                path=path_result.path,
                total_cost_minutes=path_result.total_cost,
                is_adjacent=(len(path_result.path) <= 2),
            ))
        # Sort: adjacent first, then by area, then by cost
        plans.sort(key=lambda p: (not p.is_adjacent, p.destination_area_name, p.total_cost_minutes))
        return plans

    def execute_move(self, world: WorldState, destination_key: str) -> ActionResult:
        """Execute a move to the given destination using shortest path."""
        if destination_key == world.active_location.key:
            return ActionResult(action_key="move", messages=["已经在目的地了。"])

        plan = self.plan_move(world, destination_key)
        if plan is None:
            raise ValueError(
                f"{destination_key} is not reachable from {world.active_location.key}."
            )

        destination = self.port_map.location_by_key(destination_key)
        world.active_location = PortLocation(
            key=destination.key,
            display_name=destination.display_name,
        )
        if self.time_service is not None:
            self.time_service.advance_minutes(world, plan.total_cost_minutes)
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

        messages: list[str] = []
        if len(plan.path) > 2:
            intermediate = [
                self.port_map.location_by_key(k).display_name
                for k in plan.path[1:-1]
            ]
            via = "→".join(intermediate)
            messages.append(f"途经{via}，前往了{destination.display_name}。（{plan.total_cost_minutes}分钟）")
        else:
            messages.append(f"前往了{destination.display_name}。（{plan.total_cost_minutes}分钟）")

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

    # ── Legacy compatibility ────────────────────────────────────────

    def visible_destinations(self, world: WorldState) -> tuple[str, ...]:
        """Return adjacent neighbor keys the player can navigate to."""
        return self.port_map.visible_neighbors(
            world.active_location.key,
            can_see_private=self.can_see_private(world),
        )

    def move_player(self, world: WorldState, destination_key: str) -> ActionResult:
        """Move the player (legacy entry point, delegates to execute_move)."""
        return self.execute_move(world, destination_key)
