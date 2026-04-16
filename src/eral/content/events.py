"""Load command-triggered event definitions."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class EventDefinition:
    """Static trigger definition for a lightweight event."""

    key: str
    action_key: str
    actor_tags: tuple[str, ...]
    location_keys: tuple[str, ...]
    time_slots: tuple[str, ...]
    min_affection: int | None
    min_trust: int | None
    min_obedience: int | None
    required_stage: str | None
    requires_date: bool | None
    requires_private: bool
    required_skin_key: str | None = None
    required_skin_tags: tuple[str, ...] = ()
    required_removed_slots: tuple[str, ...] = ()
    forbidden_removed_slots: tuple[str, ...] = ()
    required_marks: dict[str, int] = field(default_factory=dict)


def load_event_definitions(path: Path) -> tuple[EventDefinition, ...]:
    """Load event definitions from TOML."""

    if not path.exists():
        return ()

    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    return tuple(
        EventDefinition(
            key=item["key"],
            action_key=item["action_key"],
            actor_tags=tuple(item.get("actor_tags", [])),
            location_keys=tuple(item.get("location_keys", [])),
            time_slots=tuple(item.get("time_slots", [])),
            min_affection=(
                int(item["min_affection"]) if "min_affection" in item else None
            ),
            min_trust=int(item["min_trust"]) if "min_trust" in item else None,
            min_obedience=int(item["min_obedience"]) if "min_obedience" in item else None,
            required_stage=item.get("required_stage"),
            requires_date=item.get("requires_date"),
            requires_private=bool(item.get("requires_private", False)),
            required_skin_key=item.get("required_skin_key"),
            required_skin_tags=tuple(item.get("required_skin_tags", [])),
            required_removed_slots=tuple(item.get("required_removed_slots", [])),
            forbidden_removed_slots=tuple(item.get("forbidden_removed_slots", [])),
            required_marks={
                str(k): int(v) for k, v in item.get("required_marks", {}).items()
            },
        )
        for item in raw_data.get("events", [])
    )
