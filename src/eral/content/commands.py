"""Load starter command definitions."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

SUPPORTED_TARGET_MODES: frozenset[str] = frozenset({"actor", "player", "world"})

SUPPORTED_OPERATIONS: frozenset[str] = frozenset(
    {
        "sleep",
        "nap",
        "bathe",
        "start_training",
        "end_training",
        "remove_underwear_bottom",
        "remove_top",
        "change_position_missionary",
        "change_position_behind",
        "change_position_standing",
        "toggle_ejaculate_inside",
        "start_follow",
        "stop_follow",
        "start_date",
        "end_date",
    }
)


@dataclass(frozen=True, slots=True)
class CommandDefinition:
    """Static command-definition metadata loaded from train.toml."""

    index: int
    display_name: str
    category: str
    location_tags: tuple[str, ...]
    time_slots: tuple[str, ...]
    min_affection: int | None
    min_trust: int | None
    min_obedience: int | None
    required_stage: str | None
    operation: str | None
    requires_following: bool | None
    requires_date: bool | None
    required_removed_slots: tuple[str, ...] = ()
    training_position_keys: tuple[str, ...] = ()
    required_conditions: dict[str, int] = field(default_factory=dict)
    forbidden_conditions: tuple[str, ...] = ()
    required_marks: dict[str, int] = field(default_factory=dict)
    apply_marks: dict[str, int] = field(default_factory=dict)
    remove_marks: tuple[str, ...] = ()
    success_tiers: tuple[float, ...] = (0.1, 1.0, 2.0)
    required_items: dict[str, int] = field(default_factory=dict)
    activates_persistent_state: str | None = None
    blocked_by_persistent_states: tuple[str, ...] = ()
    resolution_key: str | None = None
    shopfront_key: str | None = None
    required_actor_tags: tuple[str, ...] = ()
    personal_income: int = 0
    elapsed_minutes: int = 10
    target_mode: str = "actor"


def load_command_definitions(path: Path) -> tuple[CommandDefinition, ...]:
    """Load command definitions from TOML.

    The runtime contract is now explicit: command definitions come only from
    ``data/base/commands/train.toml`` and use ``[[train]]`` blocks. The train
    file owns command metadata only; declarative effects belong in
    ``data/base/effects/command_effects.toml``.
    """

    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    if "train" not in raw_data:
        raise ValueError(f"{path} must define [[train]] entries")

    items = raw_data["train"]
    default_category = "train"

    return tuple(
        CommandDefinition(
            index=int(item["index"]),
            display_name=item["label"],
            category=str(item.get("category", default_category)),
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
            personal_income=int(item.get("personal_income", 0)),
            success_tiers=tuple(float(v) for v in item.get("success_tiers", [0.1, 1.0, 2.0])),
            elapsed_minutes=int(item.get("elapsed_minutes", 10)),
            target_mode=str(item.get("target_mode", "actor")),
        )
        for item in items
    )
