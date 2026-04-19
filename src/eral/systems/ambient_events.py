"""Ambient event service — roll random flavor events on time-slot advance."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from eral.content.ambient_events import AmbientEventDefinition
from eral.domain.map import PortMap
from eral.domain.world import WorldState

_ROLL_CHANCE_KEY_PREFIX = "ambient_last_"


@dataclass(slots=True)
class AmbientEventOutcome:
    """Result of rolling an ambient event."""

    key: str
    message: str
    tags: tuple[str, ...]


@dataclass(slots=True)
class AmbientEventService:
    """Roll random ambient events on time slot advancement."""

    definitions: tuple[AmbientEventDefinition, ...] = ()
    port_map: PortMap | None = None
    trigger_chance: float = 0.25
    rng: random.Random = field(default_factory=random.Random)

    def _cooldown_key(self, event_key: str) -> str:
        return f"{_ROLL_CHANCE_KEY_PREFIX}{event_key}"

    def _off_cooldown(self, world: WorldState, event: AmbientEventDefinition) -> bool:
        last_day = world.conditions.get(self._cooldown_key(event.key), -10**6)
        return world.current_day - last_day >= event.cooldown_days

    def _current_location_tags(self, world: WorldState) -> frozenset[str]:
        if self.port_map is None:
            return frozenset()
        try:
            location = self.port_map.location_by_key(world.active_location.key)
        except KeyError:
            return frozenset()
        return frozenset(location.tags)

    def _eligible(self, world: WorldState) -> list[AmbientEventDefinition]:
        slot = world.current_time_slot.value
        season_map = world.season_month_map
        season = season_map.get(world.current_month) if season_map else None
        weather = world.weather_key
        location_tags = self._current_location_tags(world)
        return [
            event
            for event in self.definitions
            if event.matches_context(slot, season, weather, location_tags)
            and self._off_cooldown(world, event)
        ]

    def roll(self, world: WorldState) -> AmbientEventOutcome | None:
        if not self.definitions:
            return None
        if self.rng.random() >= self.trigger_chance:
            return None
        eligible = self._eligible(world)
        if not eligible:
            return None
        weights = [event.weight for event in eligible]
        picked = self.rng.choices(eligible, weights=weights, k=1)[0]
        world.conditions[self._cooldown_key(picked.key)] = world.current_day
        return AmbientEventOutcome(
            key=picked.key,
            message=picked.message,
            tags=picked.tags,
        )
