"""Load weather definitions from TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class WeatherDefinition:
    key: str
    display_name: str
    base_weight: int
    movement_modifier: float
    recovery_modifier: float
    is_raining: bool
    is_storming: bool


def load_weather_definitions(path: Path) -> dict[str, WeatherDefinition]:
    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    result: dict[str, WeatherDefinition] = {}
    for item in raw.get("weather", []):
        defn = WeatherDefinition(
            key=item["key"],
            display_name=item["display_name"],
            base_weight=int(item.get("base_weight", 10)),
            movement_modifier=float(item.get("movement_modifier", 1.0)),
            recovery_modifier=float(item.get("recovery_modifier", 1.0)),
            is_raining=bool(item.get("is_raining", False)),
            is_storming=bool(item.get("is_storming", False)),
        )
        result[defn.key] = defn

    return result
