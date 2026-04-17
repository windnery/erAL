"""Map distribution service — v2 with faction routing and capacity awareness."""

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

# Base weight for tag→location matching (before faction bonus)
_TAG_BASE_WEIGHT = 2

# Time-of-day faction bias: time_slot → weight added to faction-area locations
_TIME_FACTION_BIAS: dict[str, int] = {
    "dawn": 4,
    "morning": 1,
    "afternoon": 0,
    "evening": 2,
    "night": 4,
    "late_night": 0,  # handled separately — forced home
}

# Player-bias relationship thresholds
_PLAYER_BIAS_HIGH = 700
_PLAYER_BIAS_LOW = 300
_PLAYER_BIAS_WEIGHT_HIGH = 6
_PLAYER_BIAS_WEIGHT_LOW = 2

# Capacity overflow penalty
_CAPACITY_OVERFLOW_PENALTY = 4


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

    # ── Core resolution ────────────────────────────────────────────

    def _resolve_location(self, world: WorldState, actor: CharacterState) -> str:
        # Layer 1: forced states
        if actor.is_following or actor.is_on_date:
            return world.active_location.key

        # Layer 2: work schedule
        work_location = self._active_work_location(world, actor)
        if work_location is not None:
            return work_location

        # Layer 3: meal time
        if self._is_meal_time(world, actor):
            return "cafeteria"

        definition = self.roster.get(actor.key)
        if definition is None:
            return actor.location_key

        # Layer 4: late night → forced home
        if world.current_time_slot.value == "late_night":
            return definition.home_location_key or actor.location_key

        # Layer 5: weighted idle distribution
        weights: dict[str, int] = {}

        # 5a: schedule from character.toml
        scheduled_location = definition.schedule.get(world.current_time_slot.value)
        if scheduled_location:
            self._add_weight(weights, scheduled_location, 4)

        # 5b: faction residence bias
        faction_bias = _TIME_FACTION_BIAS.get(world.current_time_slot.value, 0)
        if faction_bias > 0:
            for loc in self.port_map.locations:
                if loc.area_key == definition.residence_area_key:
                    self._add_weight(weights, loc.key, faction_bias)

        # 5c: home location bonus at night
        if world.current_time_slot.value == "night":
            self._add_weight(weights, definition.home_location_key, 3)

        # 5d: tag-based preferences — dynamic tag matching
        for tag in definition.default_activity_tags:
            for loc in self.port_map.locations:
                if tag not in loc.tags:
                    continue
                weight = _TAG_BASE_WEIGHT
                # Bonus if location is in character's own faction area
                if loc.area_key == definition.residence_area_key:
                    weight += 1
                self._add_weight(weights, loc.key, weight)

        # 5e: player proximity bias
        relationship_total = actor.affection + actor.trust
        if self._allows_player_bias(world.active_location.key):
            if relationship_total >= _PLAYER_BIAS_HIGH:
                self._add_weight(weights, world.active_location.key, _PLAYER_BIAS_WEIGHT_HIGH)
            elif relationship_total >= _PLAYER_BIAS_LOW:
                self._add_weight(weights, world.active_location.key, _PLAYER_BIAS_WEIGHT_LOW)

        # 5f: capacity overflow — penalise or remove overcrowded locations
        for loc_key in list(weights.keys()):
            loc = self.port_map.location_by_key(loc_key)
            count = self._location_population(world, loc_key)
            if count >= loc.capacity_hard:
                # Hard cap exceeded — remove from candidates, try overflow targets
                weights.pop(loc_key, None)
                for target in loc.overflow_targets:
                    self._add_weight(weights, target, 1)
            elif count >= loc.capacity_soft:
                # Soft cap exceeded — reduce weight
                weights[loc_key] = max(1, weights[loc_key] - _CAPACITY_OVERFLOW_PENALTY)

        if not weights:
            return definition.home_location_key or actor.location_key

        return max(weights.items(), key=lambda item: (item[1], item[0]))[0]

    # ── Helpers ────────────────────────────────────────────────────

    def _location_population(self, world: WorldState, location_key: str) -> int:
        """Count non-commission characters currently at a location."""
        return sum(
            1 for actor in world.characters
            if actor.location_key == location_key and not actor.is_on_commission
        )

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
