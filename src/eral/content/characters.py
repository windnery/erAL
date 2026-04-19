"""Load character roster and schedule definitions."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from eral.content.food import FoodPreferences, load_food_preferences
from eral.content.gifts import GiftPreferences, load_gift_preferences


@dataclass(frozen=True, slots=True)
class CharacterDefinition:
    """Static character metadata and coarse time-slot schedule."""

    key: str
    display_name: str
    tags: tuple[str, ...]
    initial_location: str
    schedule: dict[str, str]
    initial_stats: InitialStatOverrides
    faction_key: str = ""
    residence_area_key: str = ""
    dorm_group_key: str = ""
    home_location_key: str = ""
    default_activity_tags: tuple[str, ...] = ()
    gift_preferences: GiftPreferences = field(default_factory=GiftPreferences)
    food_preferences: FoodPreferences = field(default_factory=FoodPreferences)


@dataclass(frozen=True, slots=True)
class InitialStatOverrides:
    """Per-character initial stat overrides applied after zeroing."""

    base: dict[str, int] = field(default_factory=dict)
    palam: dict[str, int] = field(default_factory=dict)
    abl: dict[int, int] = field(default_factory=dict)
    talent: dict[int, int] = field(default_factory=dict)
    cflag: dict[int, int] = field(default_factory=dict)
    marks: dict[str, int] = field(default_factory=dict)


def _parse_initial_stats(raw: dict | None) -> InitialStatOverrides:
    if raw is None:
        return InitialStatOverrides()
    return InitialStatOverrides(
        base=dict(raw.get("base", {})),
        palam=dict(raw.get("palam", {})),
        abl={int(k): v for k, v in raw.get("abl", {}).items()},
        talent={int(k): v for k, v in raw.get("talent", {}).items()},
        cflag={int(k): v for k, v in raw.get("cflag", {}).items()},
        marks={str(k): int(v) for k, v in raw.get("marks", {}).items()},
    )


def load_character_definitions(path: Path) -> tuple[CharacterDefinition, ...]:
    """Load character roster definitions from TOML."""

    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    return tuple(
        CharacterDefinition(
            key=item["key"],
            display_name=item["display_name"],
            tags=tuple(item.get("tags", [])),
            initial_location=item["initial_location"],
            faction_key=str(item.get("faction_key", "")),
            residence_area_key=str(item.get("residence_area_key", "")),
            dorm_group_key=str(item.get("dorm_group_key", "")),
            home_location_key=str(item.get("home_location_key", "")),
            default_activity_tags=tuple(item.get("default_activity_tags", [])),
            schedule={str(key): str(value) for key, value in item.get("schedule", {}).items()},
            initial_stats=_parse_initial_stats(item.get("initial_stats")),
            gift_preferences=load_gift_preferences(item.get("gift_preferences")),
            food_preferences=load_food_preferences(item.get("food_preferences")),
        )
        for item in raw_data.get("characters", [])
    )
