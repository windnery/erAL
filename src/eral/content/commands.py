"""Load starter command definitions."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CommandDefinition:
    """Static command metadata and SOURCE payload."""

    key: str
    display_name: str
    location_tags: tuple[str, ...]
    time_slots: tuple[str, ...]
    min_affection: int | None
    min_trust: int | None
    min_obedience: int | None
    required_stage: str | None
    operation: str | None
    requires_following: bool | None
    requires_date: bool | None
    required_marks: dict[str, int]
    apply_marks: dict[str, int]
    remove_marks: tuple[str, ...]
    source: dict[str, int]
    downbase: dict[str, int]
    success_tiers: tuple[float, ...]
    category: str = "daily"


def load_command_definitions(path: Path) -> tuple[CommandDefinition, ...]:
    """Load command definitions from TOML."""

    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    return tuple(
        CommandDefinition(
            key=item["key"],
            display_name=item["display_name"],
            category=str(item.get("category", "daily")),
            location_tags=tuple(item.get("location_tags", [])),
            time_slots=tuple(item.get("time_slots", [])),
            min_affection=(
                int(item["min_affection"]) if "min_affection" in item else None
            ),
            min_trust=int(item["min_trust"]) if "min_trust" in item else None,
            min_obedience=int(item["min_obedience"]) if "min_obedience" in item else None,
            required_stage=item.get("required_stage"),
            operation=item.get("operation"),
            requires_following=item.get("requires_following"),
            requires_date=item.get("requires_date"),
            required_marks={
                str(k): int(v) for k, v in item.get("required_marks", {}).items()
            },
            apply_marks={
                str(k): int(v) for k, v in item.get("apply_marks", {}).items()
            },
            remove_marks=tuple(item.get("remove_marks", [])),
            source={str(key): int(value) for key, value in item.get("source", {}).items()},
            downbase={str(key): int(value) for key, value in item.get("downbase", {}).items()},
            success_tiers=tuple(float(v) for v in item.get("success_tiers", [0.1, 1.0, 2.0])),
        )
        for item in raw_data.get("commands", [])
    )
