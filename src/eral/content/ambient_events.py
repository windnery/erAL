"""Ambient events — random non-action-triggered occurrences on time advance."""

from __future__ import annotations

import random
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AmbientEventDefinition:
    """Random event rolled on time-slot advance."""

    key: str
    weight: int = 10
    time_slots: tuple[str, ...] = ()
    seasons: tuple[str, ...] = ()
    weather_keys: tuple[str, ...] = ()
    location_tags: tuple[str, ...] = ()
    cooldown_days: int = 3
    message: str = ""
    tags: tuple[str, ...] = ()

    def matches_context(
        self,
        time_slot: str,
        season: str | None,
        weather_key: str | None,
        location_tags: frozenset[str],
    ) -> bool:
        if self.time_slots and time_slot not in self.time_slots:
            return False
        if self.seasons and season and season not in self.seasons:
            return False
        if self.weather_keys and weather_key and weather_key not in self.weather_keys:
            return False
        if self.location_tags and not any(
            tag in location_tags for tag in self.location_tags
        ):
            return False
        return True


def load_ambient_events(path: Path) -> tuple[AmbientEventDefinition, ...]:
    if not path.exists():
        return ()
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    out: list[AmbientEventDefinition] = []
    for item in raw.get("events", []):
        out.append(
            AmbientEventDefinition(
                key=item["key"],
                weight=int(item.get("weight", 10)),
                time_slots=tuple(item.get("time_slots", [])),
                seasons=tuple(item.get("seasons", [])),
                weather_keys=tuple(item.get("weather_keys", [])),
                location_tags=tuple(item.get("location_tags", [])),
                cooldown_days=int(item.get("cooldown_days", 3)),
                message=str(item.get("message", "")),
                tags=tuple(item.get("tags", [])),
            )
        )
    return tuple(out)
