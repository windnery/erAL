"""Core loop helpers for coarse-grained day progression."""

from __future__ import annotations

from dataclasses import dataclass

from eral.domain.world import TimeSlot, WorldState
from eral.engine.events import EventBus
from eral.engine.runtime_logger import RuntimeLogger
from eral.systems.commissions import CommissionService
from eral.systems.distribution import DistributionService
from eral.systems.schedule import ScheduleService
from eral.systems.time_service import TimeService
from eral.systems.vital import VitalService


@dataclass(slots=True)
class GameLoop:
    """Minimal world progression pipeline."""

    event_bus: EventBus
    schedule_service: ScheduleService | None = None
    vital_service: VitalService | None = None
    commission_service: CommissionService | None = None
    facility_service: object | None = None
    distribution_service: DistributionService | None = None
    runtime_logger: RuntimeLogger | None = None
    time_service: TimeService | None = None

    def advance_time(self, world: WorldState) -> None:
        previous_slot = world.current_time_slot
        next_slot = previous_slot.next()

        if next_slot == TimeSlot.DAWN:
            if self.time_service is not None:
                self.time_service.advance_days(world, 1)
            else:
                world.current_day += 1

        world.current_time_slot = next_slot
        world._sync_clock_from_time_slot()
        if self.schedule_service is not None:
            self.schedule_service.refresh_world(world)
        if self.distribution_service is not None:
            self.distribution_service.refresh_world(world)
        if self.vital_service is not None:
            for character in world.characters:
                self.vital_service.natural_recovery(character, world)
        if self.commission_service is not None:
            self.commission_service.tick_slot(world)
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

    def advance_to_dawn(self, world: WorldState) -> None:
        """Advance time to next dawn, applying natural recovery each slot.

        Used when an actor faints — forces sleep until start of next day.
        """
        while True:
            previous_slot = world.current_time_slot
            next_slot = previous_slot.next()
            if next_slot == TimeSlot.DAWN:
                self.advance_time(world)
                break
            self.advance_time(world)
