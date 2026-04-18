"""Load lightweight dialogue bundles with optional scene conditions."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DialogueEntry:
    """Static dialogue lines keyed by event or action, with optional conditions."""

    key: str
    actor_key: str
    lines: tuple[str, ...]
    # Optional scene conditions — entry only matches when ALL specified conditions pass.
    required_stage: str | None = None
    time_slots: tuple[str, ...] = ()
    location_keys: tuple[str, ...] = ()
    min_affection: int | None = None
    min_trust: int | None = None
    min_obedience: int | None = None
    requires_private: bool | None = None
    requires_date: bool | None = None
    requires_following: bool | None = None
    required_skin_key: str | None = None
    required_skin_tags: tuple[str, ...] = ()
    required_removed_slots: tuple[str, ...] = ()
    forbidden_removed_slots: tuple[str, ...] = ()
    requires_training: bool | None = None
    required_training_results: tuple[str, ...] = ()
    required_marks: dict[str, int] = field(default_factory=dict)
    required_memories: dict[str, int] = field(default_factory=dict)
    priority: int = 0


def load_dialogue_entries(path: Path) -> tuple[DialogueEntry, ...]:
    """Load dialogue entries from TOML."""

    if not path.exists():
        return ()

    with path.open("rb") as handle:
        raw_data = tomllib.load(handle)

    return tuple(
        DialogueEntry(
            key=item["key"],
            actor_key=item["actor_key"],
            lines=tuple(item.get("lines", [])),
            required_stage=item.get("required_stage"),
            time_slots=tuple(item.get("time_slots", [])),
            location_keys=tuple(item.get("location_keys", [])),
            min_affection=(
                int(item["min_affection"]) if "min_affection" in item else None
            ),
            min_trust=int(item["min_trust"]) if "min_trust" in item else None,
            min_obedience=int(item["min_obedience"]) if "min_obedience" in item else None,
            requires_private=item.get("requires_private"),
            requires_date=item.get("requires_date"),
            requires_following=item.get("requires_following"),
            required_skin_key=item.get("required_skin_key"),
            required_skin_tags=tuple(item.get("required_skin_tags", [])),
            required_removed_slots=tuple(item.get("required_removed_slots", [])),
            forbidden_removed_slots=tuple(item.get("forbidden_removed_slots", [])),
            requires_training=item.get("requires_training"),
            required_training_results=tuple(item.get("required_training_results", [])),
            required_marks={
                str(k): int(v) for k, v in item.get("required_marks", {}).items()
            },
            required_memories={
                str(k): int(v) for k, v in item.get("required_memories", {}).items()
            },
            priority=int(item.get("priority", 0)),
        )
        for item in raw_data.get("entries", [])
    )
