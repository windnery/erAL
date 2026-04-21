"""Load starter command definitions."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
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
    requires_training: bool = False
    required_removed_slots: tuple[str, ...] = ()
    training_position_keys: tuple[str, ...] = ()
    required_conditions: dict[str, int] = field(default_factory=dict)
    forbidden_conditions: tuple[str, ...] = ()
    required_marks: dict[str, int] = field(default_factory=dict)
    apply_marks: dict[str, int] = field(default_factory=dict)
    remove_marks: tuple[str, ...] = ()
    source: dict[str, int] = field(default_factory=dict)
    downbase: dict[str, int] = field(default_factory=dict)
    success_tiers: tuple[float, ...] = (0.1, 1.0, 2.0)
    required_items: dict[str, int] = field(default_factory=dict)
    activates_persistent_state: str | None = None
    blocked_by_persistent_states: tuple[str, ...] = ()
    resolution_key: str | None = None
    shopfront_key: str | None = None
    required_actor_tags: tuple[str, ...] = ()
    personal_income: int = 0
    category: str = "daily"
    elapsed_minutes: int = 10


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
            required_items={
                str(key): int(value) for key, value in item.get("required_items", {}).items()
            },
            activates_persistent_state=item.get("activates_persistent_state"),
            blocked_by_persistent_states=tuple(
                str(v) for v in item.get("blocked_by_persistent_states", [])
            ),
            resolution_key=str(item["resolution_key"]) if "resolution_key" in item else None,
            shopfront_key=item.get("shopfront_key"),
            required_actor_tags=tuple(str(v) for v in item.get("required_actor_tags", [])),
            operation=item.get("operation"),
            requires_following=item.get("requires_following"),
            requires_date=item.get("requires_date"),
            requires_training=bool(item.get("requires_training", False)),
            required_removed_slots=tuple(
                str(value) for value in item.get("required_removed_slots", [])
            ),
            training_position_keys=tuple(
                str(value) for value in item.get("training_position_keys", [])
            ),
            required_conditions={
                str(k): int(v) for k, v in item.get("required_conditions", {}).items()
            },
            forbidden_conditions=tuple(str(v) for v in item.get("forbidden_conditions", [])),
            required_marks={
                str(k): int(v) for k, v in item.get("required_marks", {}).items()
            },
            apply_marks={
                str(k): int(v) for k, v in item.get("apply_marks", {}).items()
            },
            remove_marks=tuple(item.get("remove_marks", [])),
            source={str(key): int(value) for key, value in item.get("source", {}).items()},
            downbase={str(key): int(value) for key, value in item.get("downbase", {}).items()},
            personal_income=int(item.get("personal_income", 0)),
            success_tiers=tuple(float(v) for v in item.get("success_tiers", [0.1, 1.0, 2.0])),
            elapsed_minutes=int(item.get("elapsed_minutes", 10)),
        )
        for item in raw_data.get("commands", [])
    )
