"""Lightweight map distribution helpers."""

from __future__ import annotations

from dataclasses import dataclass

from eral.content.characters import CharacterDefinition
from eral.content.work_schedules import WorkScheduleDefinition
from eral.domain.map import PortMap
from eral.domain.world import CharacterState, WorldState
from eral.systems.calendar import CalendarService
from eral.systems.companions import CompanionService

_LUNCH_BASE_START = (12 * 60) + 30
_DINNER_BASE_START = 18 * 60
_MEAL_DURATION_MINUTES = 30
_MEAL_OFFSET_RANGE = 20

_TAG_LOCATION_WEIGHTS: dict[str, tuple[str, int]] = {
    "sleep": ("dormitory_a", 2),
    "food": ("cafeteria", 2),
    "garden": ("garden", 2),
    "social": ("garden", 1),
    "rest": ("garden", 1),
    "training": ("training_ground", 2),
    "harbor": ("dock", 2),
    "work": ("command_office", 2),
    "serious": ("command_office", 1),
    "cheerful": ("garden", 1),
}


@dataclass(slots=True)
class DistributionService:
    """Resolve which characters are currently present at one location."""

    roster: dict[str, CharacterDefinition]
    port_map: PortMap
    work_schedules: tuple[WorkScheduleDefinition, ...] = ()
    calendar_service: CalendarService | None = None
    companion_service: CompanionService | None = None

    def refresh_world(self, world: WorldState) -> None:
        """Refresh runtime actor locations from dynamic distribution rules."""

        for actor in world.characters:
            if actor.is_on_commission:
                continue
            new_location = self._resolve_location(world, actor)
            if new_location != actor.location_key:
                actor.previous_location_key = actor.location_key
                actor.location_key = new_location
                actor.encounter_location_key = None
        if self.companion_service is not None:
            self.companion_service.refresh_world(world)

    def present_characters(self, world: WorldState, location_key: str) -> tuple[CharacterState, ...]:
        return tuple(
            actor
            for actor in sorted(world.characters, key=self._sort_key, reverse=True)
            if actor.location_key == location_key and not actor.is_on_commission
        )

    def _resolve_location(self, world: WorldState, actor: CharacterState) -> str:
        if actor.is_following or actor.is_on_date:
            return world.active_location.key

        work_location = self._active_work_location(world, actor)
        if work_location is not None:
            return work_location

        if self._is_meal_time(world, actor):
            return "cafeteria"

        definition = self.roster.get(actor.key)
        if definition is None:
            return actor.location_key

        if world.current_time_slot.value == "late_night":
            return definition.home_location_key or actor.location_key

        weights: dict[str, int] = {}
        scheduled_location = definition.schedule.get(world.current_time_slot.value)
        if scheduled_location:
            self._add_weight(weights, scheduled_location, 4)

        if world.current_time_slot.value == "night":
            self._add_weight(weights, definition.home_location_key, 3)

        for tag in definition.default_activity_tags:
            location_key, weight = _TAG_LOCATION_WEIGHTS.get(tag, ("", 0))
            self._add_weight(weights, location_key, weight)

        relationship_total = actor.affection + actor.trust
        if self._allows_player_bias(world.active_location.key):
            if relationship_total >= 700:
                self._add_weight(weights, world.active_location.key, 6)

        if not weights:
            return definition.home_location_key or actor.location_key

        return max(weights.items(), key=lambda item: (item[1], item[0]))[0]

    def _active_work_location(self, world: WorldState, actor: CharacterState) -> str | None:
        current_minutes = world.current_hour * 60 + world.current_minute
        festival_tags = self._festival_tags(world)
        for schedule in self.work_schedules:
            if schedule.actor_key != actor.key:
                continue
            if not self._matches_rules(
                schedule,
                month=world.current_month,
                day=world.current_day,
                weekday=world.current_weekday,
                festival_tags=festival_tags,
            ):
                continue
            start_minutes = self._parse_clock_minutes(schedule.start_time)
            end_minutes = self._parse_clock_minutes(schedule.end_time)
            if start_minutes <= current_minutes < end_minutes:
                return schedule.location_key
        return None

    def _festival_tags(self, world: WorldState) -> tuple[str, ...]:
        if self.calendar_service is None:
            return ()
        return self.calendar_service.festival_tags_for_date(
            world.current_month,
            world.current_day,
        )

    def _is_meal_time(self, world: WorldState, actor: CharacterState) -> bool:
        current_minutes = world.current_hour * 60 + world.current_minute
        offset = self._stable_meal_offset(actor.key)
        for base_start in (_LUNCH_BASE_START, _DINNER_BASE_START):
            window_start = base_start + offset
            window_end = window_start + _MEAL_DURATION_MINUTES
            if window_start <= current_minutes < window_end:
                return True
        return False

    @staticmethod
    def _stable_meal_offset(actor_key: str) -> int:
        return (sum(ord(ch) for ch in actor_key) % ((_MEAL_OFFSET_RANGE * 2) + 1)) - _MEAL_OFFSET_RANGE

    def _allows_player_bias(self, location_key: str) -> bool:
        location = self.port_map.location_by_key(location_key)
        blocked_tags = {"work", "command", "core"}
        return not any(tag in blocked_tags for tag in location.tags)

    @staticmethod
    def _parse_clock_minutes(value: str) -> int:
        hour_text, minute_text = value.split(":", 1)
        return int(hour_text) * 60 + int(minute_text)

    @staticmethod
    def _matches_rules(
        schedule: WorkScheduleDefinition,
        month: int,
        day: int,
        weekday: str,
        festival_tags: tuple[str, ...],
    ) -> bool:
        rules = schedule.date_rules
        weekdays = rules.get("weekdays", ())
        if weekdays and weekday not in weekdays:
            return False
        months = rules.get("months", ())
        if months and month not in months:
            return False
        days = rules.get("days", ())
        if days and day not in days:
            return False
        required_festival_tags = rules.get("festival_tags", ())
        if required_festival_tags and not all(tag in festival_tags for tag in required_festival_tags):
            return False
        return True

    @staticmethod
    def _add_weight(weights: dict[str, int], location_key: str | None, weight: int) -> None:
        if not location_key or weight <= 0:
            return
        weights[location_key] = weights.get(location_key, 0) + weight

    @staticmethod
    def _sort_key(actor: CharacterState) -> tuple[int, int, int, str]:
        interaction_priority = 1 if actor.tags and ("shopkeeper" in actor.tags or "service_npc" in actor.tags) else 0
        relationship_priority = actor.affection + actor.trust
        return (interaction_priority, relationship_priority, actor.obedience, actor.key)
