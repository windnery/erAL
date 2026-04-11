"""Core loop helpers for coarse-grained day progression."""

from __future__ import annotations

from dataclasses import dataclass

from eral.domain.world import TimeSlot, WorldState
from eral.engine.events import EventBus
from eral.engine.runtime_logger import RuntimeLogger
from eral.systems.schedule import ScheduleService


@dataclass(slots=True)
class GameLoop:
    """Minimal world progression pipeline."""

    event_bus: EventBus
    schedule_service: ScheduleService | None = None
    runtime_logger: RuntimeLogger | None = None

    def advance_time(self, world: WorldState) -> None:
        previous_slot = world.current_time_slot
        next_slot = previous_slot.next()

        if next_slot == TimeSlot.DAWN:
            world.current_day += 1

        world.current_time_slot = next_slot
        if self.schedule_service is not None:
            self.schedule_service.refresh_world(world)
        self.event_bus.publish(
            "time.advanced",
            previous_slot=previous_slot.value,
            current_slot=world.current_time_slot.value,
            current_day=world.current_day,
        )
        if self.runtime_logger is not None:
            self.runtime_logger.append(
                kind="time_advanced",
                action_key="wait",
                actor_key=None,
                day=world.current_day,
                time_slot=world.current_time_slot.value,
                previous_time_slot=previous_slot.value,
                location_key=world.active_location.key,
                triggered_events=[],
            )
