"""Load character roster and schedule definitions."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CharacterDefinition:
    """Static character metadata and coarse time-slot schedule."""

    key: str
    display_name: str
    tags: tuple[str, ...]
    initial_location: str
    schedule: dict[str, str]
    initial_stats: InitialStatOverrides


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
            schedule={str(key): str(value) for key, value in item.get("schedule", {}).items()},
            initial_stats=_parse_initial_stats(item.get("initial_stats")),
        )
        for item in raw_data.get("characters", [])
    )
