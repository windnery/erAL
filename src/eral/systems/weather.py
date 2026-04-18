"""Weather system: state management, transitions, and modifiers."""

from __future__ import annotations

import random
from dataclasses import dataclass

from eral.content.weather import WeatherDefinition
from eral.domain.world import WorldState


@dataclass(slots=True)
class WeatherService:
    definitions: dict[str, WeatherDefinition]

    def current(self, world: WorldState) -> WeatherDefinition:
        return self.definitions.get(world.weather_key, self.definitions["clear"])

    def refresh(self, world: WorldState) -> str:
        weights = {
            k: d.base_weight for k, d in self.definitions.items()
        }
        keys = list(weights.keys())
        chosen = random.choices(keys, weights=[weights[k] for k in keys], k=1)[0]
        world.weather_key = chosen
        return chosen

    def recovery_modifier(self, world: WorldState) -> float:
        return self.current(world).recovery_modifier

    def movement_modifier(self, world: WorldState) -> float:
        return self.current(world).movement_modifier

    def is_raining(self, world: WorldState) -> bool:
        return self.current(world).is_raining

    def is_storming(self, world: WorldState) -> bool:
        return self.current(world).is_storming
